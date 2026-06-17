from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from pathlib import Path

import numpy as np
import pandas as pd

from src.data.local_loader import (
    get_factor_snapshot,
    get_index_price,
    get_industry_snapshot,
    get_instrument_snapshot,
    get_price_feature_snapshot,
    get_price_window,
    get_rebalance_dates,
    get_yield_curve,
    get_status_snapshot,
    _trading_dates,
)


def _daily_price_matrix(order_book_ids: list[str], start: str, end: str) -> pd.DataFrame:
    frames = []
    start_ts, end_ts = pd.Timestamp(start), pd.Timestamp(end)
    for sid in order_book_ids:
        px = get_price_window([sid], end, 6000)
        if px.empty:
            continue
        px = px.loc[(px["date"] >= start_ts) & (px["date"] <= end_ts), ["date", "order_book_id", "close"]]
        if not px.empty:
            frames.append(px)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames).pivot(index="date", columns="order_book_id", values="close").sort_index()


def summarize_performance(portfolio: pd.DataFrame, turnover: pd.DataFrame, config: "TrendQualityConfig") -> dict:
    ret = portfolio["daily_return"]
    nav = portfolio["nav"]
    bnav = portfolio["benchmark_nav"]
    days = max(len(ret), 1)
    ann = nav.iloc[-1] ** (252 / days) - 1
    bench_ann = bnav.iloc[-1] ** (252 / days) - 1
    vol = ret.std(ddof=0) * np.sqrt(252)
    sharpe = ann / vol if vol and not np.isnan(vol) else np.nan
    downside = ret.loc[ret < 0].std(ddof=0) * np.sqrt(252)
    sortino = ann / downside if downside and not np.isnan(downside) else np.nan
    drawdown = nav / nav.cummax() - 1
    excess = ret - bnav.pct_change().reindex(ret.index).fillna(0.0)
    ir = excess.mean() / excess.std(ddof=0) * np.sqrt(252) if excess.std(ddof=0) else np.nan
    bret = portfolio["benchmark_nav"].pct_change().fillna(0.0)
    beta = np.cov(ret, bret)[0, 1] / np.var(bret) if len(ret) > 2 and np.var(bret) else np.nan
    annual_turnover = turnover["turnover"].sum() / (days / 252) if not turnover.empty else 0.0
    return {
        "start_date": config.start_date,
        "end_date": config.end_date,
        "annual_return": float(ann),
        "benchmark_annual_return": float(bench_ann),
        "cumulative_return": float(nav.iloc[-1] - 1),
        "benchmark_cumulative_return": float(bnav.iloc[-1] - 1),
        "max_drawdown": float(drawdown.min()),
        "sharpe": float(sharpe),
        "sortino": float(sortino),
        "information_ratio": float(ir),
        "beta": float(beta),
        "annual_turnover": float(annual_turnover),
        "average_period_turnover": float(turnover["turnover"].mean()) if not turnover.empty else 0.0,
        "total_cost_drag": float(turnover["cost"].sum()) if not turnover.empty else 0.0,
        "final_nav": float(nav.iloc[-1]),
        "benchmark_final_nav": float(bnav.iloc[-1]),
        "rebalance_count": int(len(turnover)),
        "hold_count": config.hold_count,
        "sell_rank": config.sell_rank,
        "weighting": config.weighting,
    }


@dataclass(frozen=True)
class TrendQualityConfig:
    start_date: str = "2021-06-30"
    end_date: str = "2026-06-16"
    benchmark: str = "000906.XSHG"
    initial_cash: float = 1_000_000.0
    rebalance_frequency: str = "monthly"
    hold_count: int = 20
    sell_rank: int = 40
    target_gross_exposure: float = 0.98
    min_listed_trading_days: int = 273
    min_price: float = 2.0
    min_avg_turnover_20: float = 30_000_000.0
    min_market_cap: float = 3_000_000_000.0
    exclude_financials: bool = True
    weighting: str = "equal"  # equal, score, inv_vol
    trading_cost_bps: float = 15.0
    trend_weight: float = 0.45
    breakout_weight: float = 0.20
    quality_weight: float = 0.20
    risk_weight: float = 0.15
    market_timing: bool = False
    timing_ma: int = 120
    stop_by_benchmark_drawdown: float | None = None
    stock_trend_filter: str | None = None  # ma60, ma120, ma200
    stock_drawdown_stop: float | None = None
    stock_drawdown_mode: str = "daily_stop"  # daily_stop, rebalance_filter, or score_penalty
    stock_drawdown_penalty: float = 0.75
    breadth_filter: str | None = None  # ma120, ma200
    breadth_threshold: float = 0.5
    dynamic_module_weights: bool = False
    dynamic_weight_lookback: int = 6
    target_volatility: float | None = None
    vol_control_window: int = 60
    regime_filter: bool = False
    top_industries: int | None = None
    portfolio_drawdown_stop: float | None = None
    portfolio_reentry_days: int = 20
    cash_rate_column: str = "10Y"
    cash_rate_multiplier: float = 1.0


def _z(series: pd.Series) -> pd.Series:
    s = pd.to_numeric(series, errors="coerce").replace([np.inf, -np.inf], np.nan)
    if s.notna().sum() < 3:
        return pd.Series(np.nan, index=series.index)
    s = s.clip(s.quantile(0.02), s.quantile(0.98))
    std = s.std(ddof=0)
    if not std or np.isnan(std):
        return pd.Series(0.0, index=series.index)
    return (s - s.mean()) / std


def _listed_days(listed_dates: pd.Series, date: str) -> pd.Series:
    cal = _trading_dates().values
    listed = pd.to_datetime(listed_dates, errors="coerce").values
    as_of = np.datetime64(pd.Timestamp(date).normalize())
    out = np.searchsorted(cal, as_of, side="right") - np.searchsorted(cal, listed, side="left")
    out[pd.isna(listed_dates).values] = 0
    return pd.Series(out, index=listed_dates.index)


def build_universe(date: str, config: TrendQualityConfig) -> pd.DataFrame:
    inst = get_instrument_snapshot(date).set_index("order_book_id")
    status = get_status_snapshot(date).set_index("order_book_id")
    factors = get_factor_snapshot(date).drop(columns=["date"], errors="ignore")
    industry = get_industry_snapshot(date).set_index("order_book_id")
    px = get_price_feature_snapshot(date)
    df = inst.join(status, how="left").join(factors, how="left").join(px, how="left")
    if not industry.empty:
        cols = [c for c in ["sector_code", "sector_code_name", "industry_code", "industry_name"] if c in industry.columns]
        df = df.join(industry[cols], rsuffix="_industry")
    df["listed_trading_days"] = _listed_days(df["listed_date"], date)
    mask = (
        (df["type"] == "CS")
        & (df["status"] == "Active")
        & (df["special_type"].fillna("Normal") == "Normal")
        & (df["is_st"].fillna(False) == False)
        & (df["is_suspended"].fillna(False) == False)
        & (df["listed_trading_days"] >= config.min_listed_trading_days)
        & (df["close"] > config.min_price)
        & (df["avg_turnover_20"] > config.min_avg_turnover_20)
        & (df["market_cap"] > config.min_market_cap)
    )
    if config.exclude_financials and "sector_code" in df.columns:
        mask &= df["sector_code"].fillna("") != "Financials"
    return df.loc[mask].copy()


def build_scores(date: str, config: TrendQualityConfig) -> pd.DataFrame:
    df = build_universe(date, config)
    if df.empty:
        return pd.DataFrame()
    if config.top_industries is not None and "industry_name" in df.columns:
        industry_score = _industry_scores(df)
        selected = set(industry_score.head(config.top_industries).index)
        df = df.loc[df["industry_name"].isin(selected)].copy()
        if df.empty:
            return pd.DataFrame()
    scores = pd.DataFrame(index=df.index)
    trend_parts = pd.concat(
        [
            _z(df["momentum_63"]),
            _z(df["momentum_126"]),
            _z(df["momentum_252"]),
            _z(df["ma_60_ratio"]),
            _z(df["ma_120_ratio"]),
        ],
        axis=1,
    )
    scores["trend"] = trend_parts.mean(axis=1)
    breakout_parts = pd.concat([_z(df["high_252_ratio"]), _z(df["turnover_trend_20_60"])], axis=1)
    scores["breakout"] = breakout_parts.mean(axis=1)
    quality_parts = pd.concat(
        [
            _z(df["return_on_equity_ttm"]),
            _z(df["return_on_asset_ttm"]),
            _z(df["gross_profit_margin_ttm"]),
            _z(df["ocf_to_debt_ttm"]),
        ],
        axis=1,
    )
    scores["quality"] = quality_parts.mean(axis=1)
    risk_parts = pd.concat(
        [
            -_z(df["vol_120"]),
            -_z(df["downside_vol_120"]),
            _z(df["drawdown_252"]),
        ],
        axis=1,
    )
    scores["risk"] = risk_parts.mean(axis=1)
    weights = _module_weights(date, config)
    scores["score"] = sum(weights[col] * scores[col] for col in ["trend", "breakout", "quality", "risk"])
    scores["vol_120"] = df["vol_120"]
    scores["market_cap"] = df["market_cap"]
    for col in ["sector_code", "sector_code_name", "industry_code", "industry_name"]:
        if col in df.columns:
            scores[col] = df[col]
    scores = scores.replace([np.inf, -np.inf], np.nan).dropna(subset=["score"])
    if config.stock_drawdown_stop is not None and config.stock_drawdown_mode == "score_penalty":
        drawdown = df.loc[scores.index, "drawdown_252"]
        scores.loc[drawdown < config.stock_drawdown_stop, "score"] -= config.stock_drawdown_penalty
    if config.stock_drawdown_stop is not None and config.stock_drawdown_mode == "rebalance_filter":
        scores = scores.loc[scores["risk"].notna()].copy()
        drawdown = df.loc[scores.index, "drawdown_252"]
        scores = scores.loc[drawdown >= config.stock_drawdown_stop].copy()
        if scores.empty:
            return scores
    scores["rank"] = scores["score"].rank(ascending=False, method="first")
    return scores.sort_values("rank")


def _industry_scores(df: pd.DataFrame) -> pd.Series:
    grouped = df.groupby("industry_name", dropna=False)
    industry = pd.DataFrame(
        {
            "momentum": grouped["momentum_126"].median(),
            "breadth": grouped["ma_120_ratio"].apply(lambda x: (x >= 0).mean()),
            "low_vol": -grouped["vol_120"].median(),
            "size": grouped.size(),
        }
    )
    industry = industry.loc[industry["size"] >= 10].copy()
    if industry.empty:
        return pd.Series(dtype=float)
    score = _z(industry["momentum"]) + _z(industry["breadth"]) + _z(industry["low_vol"])
    return score.sort_values(ascending=False)


def _module_weights(date: str, config: TrendQualityConfig) -> dict[str, float]:
    base = {
        "trend": config.trend_weight,
        "breakout": config.breakout_weight,
        "quality": config.quality_weight,
        "risk": config.risk_weight,
    }
    if not config.dynamic_module_weights:
        return base
    dates = get_rebalance_dates(config.start_date, date, config.rebalance_frequency)
    if len(dates) <= config.dynamic_weight_lookback:
        return base
    recent = dates[-config.dynamic_weight_lookback - 1 : -1]
    rows = []
    for d in recent:
        sc = _raw_module_scores(d, config)
        if sc.empty:
            continue
        next_dates = get_rebalance_dates(d, config.end_date, config.rebalance_frequency)
        if len(next_dates) < 2:
            continue
        next_d = next_dates[1]
        px0 = get_price_feature_snapshot(d)["close"]
        px1 = get_price_feature_snapshot(next_d)["close"]
        fwd = px1 / px0 - 1
        for col in ["trend", "breakout", "quality", "risk"]:
            valid = sc[col].notna() & fwd.reindex(sc.index).notna()
            if valid.sum() > 50:
                rows.append({"module": col, "ic": sc.loc[valid, col].corr(fwd.reindex(sc.index).loc[valid])})
    if not rows:
        return base
    ic = pd.DataFrame(rows).groupby("module")["ic"].mean().reindex(["trend", "breakout", "quality", "risk"]).fillna(0.0)
    positive = ic.clip(lower=0)
    if positive.sum() <= 0:
        return base
    raw = 0.3 * pd.Series(base) + 0.7 * (positive / positive.sum())
    return (raw / raw.sum()).to_dict()


def _raw_module_scores(date: str, config: TrendQualityConfig) -> pd.DataFrame:
    cfg = replace(config, dynamic_module_weights=False)
    df = build_universe(date, cfg)
    if df.empty:
        return pd.DataFrame()
    scores = pd.DataFrame(index=df.index)
    scores["trend"] = pd.concat([_z(df["momentum_63"]), _z(df["momentum_126"]), _z(df["momentum_252"]), _z(df["ma_60_ratio"]), _z(df["ma_120_ratio"])], axis=1).mean(axis=1)
    scores["breakout"] = pd.concat([_z(df["high_252_ratio"]), _z(df["turnover_trend_20_60"])], axis=1).mean(axis=1)
    scores["quality"] = pd.concat([_z(df["return_on_equity_ttm"]), _z(df["return_on_asset_ttm"]), _z(df["gross_profit_margin_ttm"]), _z(df["ocf_to_debt_ttm"])], axis=1).mean(axis=1)
    scores["risk"] = pd.concat([-_z(df["vol_120"]), -_z(df["downside_vol_120"]), _z(df["drawdown_252"])], axis=1).mean(axis=1)
    return scores


def _target_weights(scores: pd.DataFrame, current: set[str], config: TrendQualityConfig) -> pd.Series:
    if scores.empty:
        return pd.Series(dtype=float)
    rank = scores["rank"]
    keep = [sid for sid in current if sid in rank.index and rank.loc[sid] <= config.sell_rank]
    buy = scores.loc[~scores.index.isin(keep)].head(max(0, config.hold_count - len(keep))).index.tolist()
    target = keep + buy
    if len(target) > config.hold_count:
        target = list(scores.loc[target].sort_values("rank").head(config.hold_count).index)
    if not target:
        return pd.Series(dtype=float)
    sub = scores.loc[target]
    if config.weighting == "equal":
        raw = pd.Series(1.0, index=target)
    elif config.weighting == "score":
        raw = (sub["score"] - sub["score"].min()).clip(lower=0) + 0.05
    elif config.weighting == "inv_vol":
        raw = 1.0 / sub["vol_120"].replace(0, np.nan)
        raw = raw.replace([np.inf, -np.inf], np.nan).fillna(raw.median())
    else:
        raise ValueError(config.weighting)
    return raw / raw.sum() * config.target_gross_exposure


def _timing_exposure(config: TrendQualityConfig, dates: pd.DatetimeIndex) -> pd.Series:
    exposure = pd.Series(config.target_gross_exposure, index=dates)
    if not config.market_timing and config.stop_by_benchmark_drawdown is None:
        return exposure
    benchmark = get_index_price(config.benchmark, config.start_date, config.end_date).set_index("date")["close"].reindex(dates).ffill()
    if config.market_timing:
        ma = benchmark.rolling(config.timing_ma, min_periods=max(20, config.timing_ma // 3)).mean()
        exposure = exposure.where(benchmark >= ma, 0.0)
    if config.stop_by_benchmark_drawdown is not None:
        dd = benchmark / benchmark.rolling(252, min_periods=60).max() - 1
        exposure = exposure.where(dd >= config.stop_by_benchmark_drawdown, 0.0)
    if config.regime_filter:
        ma200 = benchmark.rolling(200, min_periods=60).mean()
        ma60 = benchmark.rolling(60, min_periods=20).mean()
        breadth = _market_breadth_exposure(TrendQualityConfig(**{**asdict(config), "regime_filter": False}), dates)
        exposure = exposure.where((benchmark >= ma200) & (ma60 >= ma200) & (breadth > 0), 0.0)
    return exposure.fillna(config.target_gross_exposure)


def _market_breadth_exposure(config: TrendQualityConfig, dates: pd.DatetimeIndex) -> pd.Series:
    exposure = pd.Series(config.target_gross_exposure, index=dates)
    if not config.breadth_filter:
        return exposure
    ratio_col = {"ma120": "ma_120_ratio", "ma60": "ma_60_ratio"}.get(config.breadth_filter)
    if ratio_col is None:
        ratio_col = "ma_120_ratio"
    breadth_values = {}
    for date in get_rebalance_dates(config.start_date, config.end_date, config.rebalance_frequency):
        try:
            universe = build_universe(date, config)
        except KeyError:
            continue
        if universe.empty or ratio_col not in universe.columns:
            continue
        breadth_values[pd.Timestamp(date)] = (universe[ratio_col] >= 0).mean()
    breadth = pd.Series(breadth_values).sort_index().reindex(dates).ffill()
    return exposure.where(breadth >= config.breadth_threshold, 0.0).fillna(0.0)


def run_backtest(config: TrendQualityConfig, output_dir: str | Path | None = None) -> dict:
    dates = get_rebalance_dates(config.start_date, config.end_date, config.rebalance_frequency)
    snapshots, targets = {}, {}
    all_ids: set[str] = set()
    current: set[str] = set()
    for date in dates:
        scores = build_scores(date, config)
        weights = _target_weights(scores, current, config)
        snapshots[date] = scores
        targets[date] = weights
        all_ids.update(weights.index.tolist())
        current = set(weights.index)
    price = _daily_price_matrix(sorted(all_ids), config.start_date, config.end_date)
    if price.empty:
        raise RuntimeError("empty price matrix")
    returns = price.pct_change().fillna(0.0)
    raw_daily_weights = pd.DataFrame(0.0, index=returns.index, columns=returns.columns)
    timing = _timing_exposure(config, returns.index)
    timing = np.minimum(timing, _market_breadth_exposure(config, returns.index))
    turnover_records = []
    prev = pd.Series(dtype=float)
    cost_rate = config.trading_cost_bps / 10000.0
    for date, target in targets.items():
        ts = returns.index[returns.index >= pd.Timestamp(date)]
        if ts.empty:
            continue
        effective = ts[0]
        aligned_prev = prev.reindex(raw_daily_weights.columns).fillna(0.0)
        aligned_target = target.reindex(raw_daily_weights.columns).fillna(0.0)
        turnover = (aligned_target - aligned_prev).abs().sum()
        turnover_records.append({"date": effective, "turnover": turnover, "cost": turnover * cost_rate, "reason": "rebalance"})
        raw_daily_weights.loc[effective:, :] = aligned_target.values
        prev = target
    exposure_scale = (timing / config.target_gross_exposure).replace([np.inf, -np.inf], 0.0).fillna(0.0)
    daily_weights = raw_daily_weights.mul(exposure_scale, axis=0)
    use_daily_stock_stop = config.stock_drawdown_stop is not None and config.stock_drawdown_mode == "daily_stop"
    if config.stock_trend_filter or use_daily_stock_stop:
        stock_mask = pd.DataFrame(True, index=price.index, columns=price.columns)
        if config.stock_trend_filter:
            window = int(config.stock_trend_filter.replace("ma", ""))
            ma = price.rolling(window, min_periods=max(20, window // 3)).mean()
            stock_mask &= price >= ma
        if use_daily_stock_stop:
            peak = price.rolling(252, min_periods=60).max()
            dd = price / peak - 1
            stock_mask &= dd >= config.stock_drawdown_stop
        daily_weights = daily_weights.where(stock_mask, 0.0)
    if config.target_volatility is not None:
        prelim_ret = (daily_weights.shift(1).fillna(0.0) * returns).sum(axis=1)
        realized_vol = prelim_ret.rolling(config.vol_control_window, min_periods=20).std() * np.sqrt(252)
        vol_scale = (config.target_volatility / realized_vol).clip(upper=1.0).fillna(1.0)
        daily_weights = daily_weights.mul(vol_scale, axis=0)
    if config.portfolio_drawdown_stop is not None:
        prelim_ret = (daily_weights.shift(1).fillna(0.0) * returns).sum(axis=1)
        prelim_nav = (1 + prelim_ret).cumprod()
        prelim_dd = prelim_nav / prelim_nav.cummax() - 1
        risk_on = pd.Series(True, index=daily_weights.index)
        off_until = None
        for date in daily_weights.index:
            if off_until is not None and date <= off_until:
                risk_on.loc[date] = False
                continue
            if prelim_dd.loc[date] < config.portfolio_drawdown_stop:
                off_until = date + pd.Timedelta(days=config.portfolio_reentry_days)
                risk_on.loc[date] = False
        daily_weights = daily_weights.where(risk_on, 0.0)
    timing_turnover = daily_weights.diff().abs().sum(axis=1)
    if not timing_turnover.empty:
        rebalance_dates = {pd.Timestamp(r["date"]) for r in turnover_records}
        for date, value in timing_turnover.items():
            if value > 1e-12 and date not in rebalance_dates:
                turnover_records.append({"date": date, "turnover": value, "cost": value * cost_rate, "reason": "timing"})
    port_ret = (daily_weights.shift(1).fillna(0.0) * returns).sum(axis=1)
    turnover_df = pd.DataFrame(turnover_records).set_index("date").sort_index() if turnover_records else pd.DataFrame(columns=["turnover", "cost", "reason"])
    if not turnover_df.empty:
        port_ret.loc[turnover_df.index] -= turnover_df["cost"]
    nav = (1 + port_ret).cumprod()
    if config.target_volatility is not None:
        rf = get_yield_curve(config.start_date, config.end_date).set_index("date")
        col = config.cash_rate_column if config.cash_rate_column in rf.columns else "10Y"
        rf_rate = rf[col].reindex(nav.index).ffill().fillna(0.0)
        cash_weight = 1 - daily_weights.sum(axis=1).shift(1).fillna(1.0)
        port_ret = port_ret + cash_weight * rf_rate * config.cash_rate_multiplier / 252.0
        nav = (1 + port_ret).cumprod()
    benchmark = get_index_price(config.benchmark, config.start_date, config.end_date).set_index("date")["close"]
    bret = benchmark.pct_change().reindex(nav.index).fillna(0.0)
    bnav = (1 + bret).cumprod()
    portfolio = pd.DataFrame({"portfolio_value": nav * config.initial_cash, "nav": nav, "daily_return": port_ret, "benchmark_nav": bnav})
    summary = summarize_performance(portfolio, turnover_df, config)
    positions = daily_weights[daily_weights.sum(axis=1) > 0].stack().rename("weight").reset_index()
    positions = positions.loc[positions["weight"] > 0].rename(columns={"level_1": "order_book_id"})
    score_frames = []
    for date, scores in snapshots.items():
        if not scores.empty:
            frame = scores.copy()
            frame["date"] = date
            score_frames.append(frame.reset_index(names="order_book_id"))
    scores_out = pd.concat(score_frames, ignore_index=True) if score_frames else pd.DataFrame()
    result = {"portfolio": portfolio, "turnover": turnover_df, "positions": positions, "scores": scores_out, "summary": summary, "config": asdict(config)}
    if output_dir is not None:
        path = Path(output_dir)
        path.mkdir(parents=True, exist_ok=True)
        portfolio.to_csv(path / "portfolio.csv", encoding="utf-8-sig")
        turnover_df.to_csv(path / "turnover.csv", encoding="utf-8-sig")
        positions.to_csv(path / "stock_positions.csv", index=False, encoding="utf-8-sig")
        scores_out.to_csv(path / "factor_scores.csv", index=False, encoding="utf-8-sig")
        pd.Series(summary).to_csv(path / "summary.csv", encoding="utf-8-sig")
        pd.Series(asdict(config)).to_csv(path / "config.csv", encoding="utf-8-sig")
    return result


def variant_config(base: TrendQualityConfig, **kwargs) -> TrendQualityConfig:
    return replace(base, **kwargs)

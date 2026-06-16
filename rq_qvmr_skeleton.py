import numpy as np
import pandas as pd
import rqdatac
from rqalpha.api import *


def init(context):
    rqdatac.init()
    context.hold_count = 30
    context.sell_rank = 60
    context.min_listed_days = 180
    context.min_market_cap = 2_000_000_000
    context.min_price = 2
    context.min_avg_turnover = 20_000_000
    context.rebalance_done = set()
    context.max_universe_size = 800
    context.sample_universe = [
        "000001.XSHE",
        "002891.XSHE",
        "600185.XSHG",
        "600000.XSHG",
    ]
    update_universe(context.sample_universe)


def handle_bar(context, bar_dict):
    now = context.now
    month_key = now.strftime("%Y-%m")
    if month_key in context.rebalance_done:
        return
    context.rebalance_done.add(month_key)
    rebalance(context, bar_dict)


def rebalance(context, bar_dict):
    universe = build_universe(context, bar_dict)
    logger.info("rebalance universe size: {}".format(len(universe)))
    if len(universe) < context.hold_count:
        universe = fallback_universe(context, bar_dict)
        logger.info("fallback universe size: {}".format(len(universe)))
    if len(universe) < 5:
        return

    scores = build_scores(universe, context.now.date())
    if scores.empty:
        return

    target_count = min(context.hold_count, len(scores))
    target = scores.sort_values("score", ascending=False).head(target_count)
    score_rank = scores["rank"].to_dict()

    for order_book_id, position in context.portfolio.positions.items():
        rank = score_rank.get(order_book_id)
        if rank is None or rank > context.sell_rank or order_book_id not in set(scores.index):
            order_target_percent(order_book_id, 0)

    weight = 0.98 / len(target)
    for order_book_id in target.index:
        order_target_percent(order_book_id, weight)


def build_universe(context, bar_dict):
    today = context.now.date()
    instruments = rqdatac.all_instruments(type="CS", market="cn")
    instruments = instruments[
        (instruments["status"] == "Active")
        & (instruments["special_type"] == "Normal")
        & (instruments["listed_date"].notna())
    ].copy()
    instruments["listed_date"] = pd.to_datetime(instruments["listed_date"]).dt.date
    instruments = instruments[
        instruments["listed_date"].map(lambda d: (today - d).days >= context.min_listed_days)
    ]
    ids = instruments["order_book_id"].tolist()

    ids = [i for i in ids if i in bar_dict]
    if not ids:
        return []

    factors = rqdatac.get_factor(ids, ["market_cap"], date=today)
    factors = factors.reset_index().set_index("order_book_id")
    ids = factors[factors["market_cap"] > context.min_market_cap].index.tolist()
    ids = ids[:context.max_universe_size]

    start_date = pd.Timestamp(today) - pd.Timedelta(days=45)
    price_df = rqdatac.get_price(
        ids,
        start_date=start_date,
        end_date=today,
        frequency="1d",
        fields=["close", "total_turnover"],
    )
    if price_df is None or price_df.empty:
        return ids
    close = price_df["close"].unstack("order_book_id").iloc[-1]
    turnover = price_df["total_turnover"].unstack("order_book_id").tail(20).mean()
    liquid = close[(close > context.min_price) & (turnover > context.min_avg_turnover)].index.tolist()
    return liquid


def fallback_universe(context, bar_dict):
    today = context.now.date()
    instruments = rqdatac.all_instruments(type="CS", market="cn")
    instruments = instruments[
        (instruments["status"] == "Active")
        & (instruments["special_type"] == "Normal")
        & (instruments["listed_date"].notna())
    ].copy()
    instruments["listed_date"] = pd.to_datetime(instruments["listed_date"]).dt.date
    instruments = instruments[
        instruments["listed_date"].map(lambda d: (today - d).days >= context.min_listed_days)
    ]
    ids = instruments["order_book_id"].tolist()
    ids = [i for i in ids if i in bar_dict]
    if not ids:
        return [i for i in context.sample_universe if i in bar_dict and not bar_dict[i].is_suspended]
    return ids[:context.max_universe_size]


def build_scores(order_book_ids, date):
    factor_names = [
        "return_on_equity_ttm",
        "return_on_asset_ttm",
        "gross_profit_margin_ttm",
        "market_cap",
        "pe_ratio_ttm",
        "pb_ratio_ttm",
        "book_to_market_ratio_ttm",
    ]
    df = rqdatac.get_factor(order_book_ids, factor_names, date=date)
    if df is None or df.empty:
        return pd.DataFrame()
    df = df.reset_index().set_index("order_book_id")

    close_df = rqdatac.get_price(order_book_ids, start_date=pd.Timestamp(date) - pd.Timedelta(days=250),
                                end_date=date, frequency="1d", fields=["close"])
    momentum = calc_momentum(close_df)
    risk = calc_risk(close_df)
    df = df.join(momentum).join(risk)

    score_df = pd.DataFrame(index=df.index)
    quality_parts = pd.concat([
        z(df["return_on_equity_ttm"]),
        z(df["return_on_asset_ttm"]),
        z(df["gross_profit_margin_ttm"]),
    ], axis=1)
    value_parts = pd.concat([
        z(df["book_to_market_ratio_ttm"]),
        -z(df["pe_ratio_ttm"]),
        -z(df["pb_ratio_ttm"]),
    ], axis=1)
    score_df["quality"] = quality_parts.mean(axis=1, skipna=True)
    score_df["value"] = value_parts.mean(axis=1, skipna=True)
    score_df["momentum"] = z(df["momentum_120"])
    score_df["risk"] = -z(df["vol_120"])
    score_df["score"] = (
        0.35 * score_df["quality"]
        + 0.25 * score_df["value"]
        + 0.25 * score_df["momentum"]
        + 0.15 * score_df["risk"]
    )
    score_df = score_df.replace([np.inf, -np.inf], np.nan).dropna(subset=["score"])
    score_df["rank"] = score_df["score"].rank(ascending=False, method="first")
    return score_df


def calc_momentum(close_df):
    close = close_df["close"].unstack("order_book_id")
    ret = close.iloc[-21] / close.iloc[-121] - 1 if len(close) >= 121 else close.iloc[-1] / close.iloc[0] - 1
    return pd.DataFrame({"momentum_120": ret})


def calc_risk(close_df):
    close = close_df["close"].unstack("order_book_id")
    returns = close.pct_change().tail(120)
    vol = returns.std()
    return pd.DataFrame({"vol_120": vol})


def z(series):
    s = pd.to_numeric(series, errors="coerce")
    lower, upper = s.quantile(0.01), s.quantile(0.99)
    s = s.clip(lower, upper)
    std = s.std()
    if std == 0 or np.isnan(std):
        return s * 0
    return (s - s.mean()) / std

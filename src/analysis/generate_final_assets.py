from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
RESULTS = {
    "5y": ROOT / "reports" / "local_backtests" / "final_enhanced_ma240_tv08_5y",
    "max": ROOT / "reports" / "local_backtests" / "final_enhanced_ma240_tv08_max",
}
OUT = ROOT / "reports" / "final_strategy_assets"


def _load_summary(path: Path) -> pd.Series:
    return pd.read_csv(path / "summary.csv", index_col=0, header=None).squeeze("columns")


def _load_portfolio(path: Path) -> pd.DataFrame:
    portfolio = pd.read_csv(path / "portfolio.csv")
    if "date" not in portfolio.columns:
        portfolio = portfolio.rename(columns={portfolio.columns[0]: "date"})
    portfolio["date"] = pd.to_datetime(portfolio["date"])
    return portfolio.set_index("date").sort_index()


def _load_positions(path: Path) -> pd.DataFrame:
    positions = pd.read_csv(path / "stock_positions.csv")
    positions["date"] = pd.to_datetime(positions["date"])
    return positions


def _load_turnover(path: Path) -> pd.DataFrame:
    turnover = pd.read_csv(path / "turnover.csv")
    if turnover.empty:
        return turnover
    turnover["date"] = pd.to_datetime(turnover["date"])
    return turnover


def _drawdown(nav: pd.Series) -> pd.Series:
    return nav / nav.cummax() - 1.0


def _plot_nav(label: str, portfolio: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    portfolio[["nav", "benchmark_nav"]].plot(ax=ax, linewidth=1.8)
    ax.set_title(f"Final Strategy NAV - {label.upper()}")
    ax.set_ylabel("Net Asset Value")
    ax.set_xlabel("")
    ax.legend(["Strategy", "Benchmark"])
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(OUT / f"nav_{label}.png", dpi=180)
    plt.close(fig)


def _plot_drawdown(label: str, portfolio: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(10, 4))
    _drawdown(portfolio["nav"]).plot(ax=ax, linewidth=1.6, color="#b23a48")
    ax.set_title(f"Final Strategy Drawdown - {label.upper()}")
    ax.set_ylabel("Drawdown")
    ax.set_xlabel("")
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(OUT / f"drawdown_{label}.png", dpi=180)
    plt.close(fig)


def _yearly_return(portfolio: pd.DataFrame) -> pd.DataFrame:
    strategy = (1 + portfolio["daily_return"]).groupby(portfolio.index.year).prod() - 1
    benchmark = portfolio["benchmark_nav"].pct_change().fillna(0)
    benchmark = (1 + benchmark).groupby(benchmark.index.year).prod() - 1
    return pd.DataFrame({"strategy_return": strategy, "benchmark_return": benchmark})


def _plot_yearly(label: str, yearly: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(10, 4.5))
    yearly.plot(kind="bar", ax=ax, width=0.78)
    ax.set_title(f"Yearly Return - {label.upper()}")
    ax.set_xlabel("")
    ax.set_ylabel("Return")
    ax.legend(["Strategy", "Benchmark"])
    ax.grid(True, axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(OUT / f"yearly_return_{label}.png", dpi=180)
    plt.close(fig)


def _holding_stats(label: str, positions: pd.DataFrame) -> pd.Series:
    counts = positions.groupby("date")["order_book_id"].nunique()
    stats = pd.Series(
        {
            "min_holding_count": counts.min(),
            "median_holding_count": counts.median(),
            "max_holding_count": counts.max(),
            "days_below_25": (counts < 25).sum(),
        },
        name=label,
    )
    counts.to_csv(OUT / f"holding_count_{label}.csv", encoding="utf-8-sig")
    return stats


def _turnover_stats(label: str, turnover: pd.DataFrame) -> pd.Series:
    if turnover.empty:
        stats = pd.Series({"total_turnover": 0.0, "total_cost_drag": 0.0, "timing_turnover_rows": 0}, name=label)
    else:
        stats = pd.Series(
            {
                "total_turnover": turnover["turnover"].sum(),
                "total_cost_drag": turnover["cost"].sum(),
                "timing_turnover_rows": (turnover.get("reason", "") == "timing").sum(),
            },
            name=label,
        )
    turnover.to_csv(OUT / f"turnover_detail_{label}.csv", index=False, encoding="utf-8-sig")
    return stats


def _score_diagnostics(label: str, path: Path) -> None:
    scores = pd.read_csv(path / "factor_scores.csv")
    module_cols = [c for c in ["trend", "breakout", "quality", "risk", "score", "market_cap"] if c in scores.columns]
    corr = scores[module_cols].corr()
    corr.to_csv(OUT / f"factor_correlation_{label}.csv", encoding="utf-8-sig")

    if "date" in scores.columns:
        scores["date"] = pd.to_datetime(scores["date"])
    if "market_cap" in scores.columns:
        mcap_corr_rows = []
        for date, group in scores.groupby("date"):
            ln_mcap = np.log(group["market_cap"].replace(0, np.nan))
            for col in [c for c in ["trend", "breakout", "quality", "risk", "score"] if c in scores.columns]:
                mcap_corr_rows.append({"date": date, "module": col, "corr_ln_mcap": group[col].corr(ln_mcap)})
        pd.DataFrame(mcap_corr_rows).to_csv(OUT / f"module_market_cap_correlation_{label}.csv", index=False, encoding="utf-8-sig")

    if "industry_name" in scores.columns:
        top_industry = (
            scores.loc[scores["rank"] <= 30]
            .groupby(["date", "industry_name"], dropna=False)
            .size()
            .rename("holding_count")
            .reset_index()
        )
        top_industry.to_csv(OUT / f"industry_exposure_rebalance_{label}.csv", index=False, encoding="utf-8-sig")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    summary_rows = []
    holding_rows = []
    turnover_rows = []

    for label, path in RESULTS.items():
        summary = _load_summary(path)
        portfolio = _load_portfolio(path)
        positions = _load_positions(path)
        turnover = _load_turnover(path)

        _plot_nav(label, portfolio)
        _plot_drawdown(label, portfolio)
        yearly = _yearly_return(portfolio)
        yearly.to_csv(OUT / f"yearly_return_{label}.csv", encoding="utf-8-sig")
        _plot_yearly(label, yearly)

        summary.name = label
        summary_rows.append(summary)
        holding_rows.append(_holding_stats(label, positions))
        turnover_rows.append(_turnover_stats(label, turnover))
        _score_diagnostics(label, path)

    pd.DataFrame(summary_rows).to_csv(OUT / "final_summary_table.csv", encoding="utf-8-sig")
    pd.DataFrame(holding_rows).to_csv(OUT / "holding_count_summary.csv", encoding="utf-8-sig")
    pd.DataFrame(turnover_rows).to_csv(OUT / "turnover_cost_summary.csv", encoding="utf-8-sig")


if __name__ == "__main__":
    main()

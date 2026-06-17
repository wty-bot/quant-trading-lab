from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "reports" / "final_strategy_assets"


SENSITIVITY_PATHS = {
    "target_volatility": ROOT / "reports" / "local_backtests" / "quarterly_vol_test",
    "timing_ma": ROOT / "reports" / "local_backtests" / "tv08_timing_test",
    "turnover_structure": ROOT / "reports" / "local_backtests" / "structural_turnover_test",
}


def _read_summary(path: Path) -> dict:
    summary = pd.read_csv(path / "summary.csv", index_col=0, header=None).squeeze("columns")
    return {
        "annual_return": float(summary["annual_return"]),
        "max_drawdown": float(summary["max_drawdown"]),
        "sharpe": float(summary["sharpe"]),
        "sortino": float(summary["sortino"]),
        "information_ratio": float(summary["information_ratio"]),
        "annual_turnover": float(summary["annual_turnover"]),
        "final_nav": float(summary["final_nav"]),
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for family, root in SENSITIVITY_PATHS.items():
        if not root.exists():
            continue
        for summary_path in root.rglob("summary.csv"):
            run_dir = summary_path.parent
            name = run_dir.name
            period = "5y" if name.endswith("_5y") else "max" if name.endswith("_max") else ""
            if not period:
                continue
            variant = name.removesuffix("_5y").removesuffix("_max")
            row = {"family": family, "variant": variant, "period": period, "path": str(run_dir.relative_to(ROOT))}
            row.update(_read_summary(run_dir))
            rows.append(row)
    table = pd.DataFrame(rows).sort_values(["family", "variant", "period"])
    table.to_csv(OUT / "sensitivity_summary.csv", index=False, encoding="utf-8-sig")

    pivot = table.pivot_table(
        index=["family", "variant"],
        columns="period",
        values=["annual_return", "max_drawdown", "sharpe", "annual_turnover"],
        aggfunc="first",
    )
    pivot.to_csv(OUT / "sensitivity_pivot.csv", encoding="utf-8-sig")


if __name__ == "__main__":
    main()

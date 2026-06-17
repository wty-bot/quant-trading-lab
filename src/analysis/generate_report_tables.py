from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results" / "tables"
SUBMIT = ROOT / "final_submission_assets" / "result_tables"


def ranking_system_table() -> pd.DataFrame:
    rows = [
        {
            "module": "趋势",
            "module_weight": "45%",
            "factor": "63日动量",
            "direction": "越高越好",
            "definition": "过去约3个月收盘价收益率",
            "logic": "捕捉中期趋势延续",
        },
        {
            "module": "趋势",
            "module_weight": "45%",
            "factor": "126日动量",
            "direction": "越高越好",
            "definition": "过去约6个月收盘价收益率",
            "logic": "识别较稳定的阶段强势",
        },
        {
            "module": "趋势",
            "module_weight": "45%",
            "factor": "252日动量",
            "direction": "越高越好",
            "definition": "过去约12个月收盘价收益率",
            "logic": "捕捉长期趋势与资金偏好",
        },
        {
            "module": "趋势",
            "module_weight": "45%",
            "factor": "MA60/MA120相对强度",
            "direction": "越高越好",
            "definition": "收盘价相对60日、120日均线的位置",
            "logic": "过滤均线下方的弱势股票",
        },
        {
            "module": "突破",
            "module_weight": "20%",
            "factor": "252日高点接近度",
            "direction": "越高越好",
            "definition": "当前价格相对过去252日最高价的位置",
            "logic": "价格接近新高通常代表趋势确认",
        },
        {
            "module": "突破",
            "module_weight": "20%",
            "factor": "20/60日成交额趋势",
            "direction": "越高越好",
            "definition": "20日平均成交额相对60日平均成交额",
            "logic": "成交活跃度改善代表资金关注上升",
        },
        {
            "module": "质量",
            "module_weight": "20%",
            "factor": "ROE、ROA",
            "direction": "越高越好",
            "definition": "净资产收益率、总资产收益率",
            "logic": "衡量盈利能力和资产使用效率",
        },
        {
            "module": "质量",
            "module_weight": "20%",
            "factor": "毛利率",
            "direction": "越高越好",
            "definition": "营业收入中的毛利占比",
            "logic": "反映商业模式质量和产品竞争力",
        },
        {
            "module": "质量",
            "module_weight": "20%",
            "factor": "经营现金流/债务",
            "direction": "越高越好",
            "definition": "经营现金流相对债务规模",
            "logic": "反映利润质量和偿债安全边际",
        },
        {
            "module": "风险",
            "module_weight": "15%",
            "factor": "120日波动率",
            "direction": "越低越好",
            "definition": "过去120个交易日收益率标准差",
            "logic": "降低组合暴露于高波动股票",
        },
        {
            "module": "风险",
            "module_weight": "15%",
            "factor": "120日下行波动率",
            "direction": "越低越好",
            "definition": "过去120个交易日负收益波动",
            "logic": "重点控制下跌方向风险",
        },
        {
            "module": "风险",
            "module_weight": "15%",
            "factor": "252日回撤",
            "direction": "回撤越小越好",
            "definition": "当前价格相对过去252日高点的回撤",
            "logic": "避免持有趋势明显破坏的股票",
        },
    ]
    return pd.DataFrame(rows)


def sample_holdings() -> pd.DataFrame:
    positions = pd.read_csv(ROOT / "results" / "final_backtests" / "5y" / "stock_positions.csv", parse_dates=["date"])
    scores = pd.read_csv(ROOT / "results" / "final_backtests" / "5y" / "factor_scores.csv", parse_dates=["date"])
    sample_date = positions.groupby("date")["order_book_id"].nunique().loc[lambda x: x >= 30].index[-1]
    merged = positions.loc[positions["date"] == sample_date].merge(
        scores[
            [
                "date",
                "order_book_id",
                "rank",
                "score",
                "trend",
                "breakout",
                "quality",
                "risk",
                "industry_name",
            ]
        ],
        on=["date", "order_book_id"],
        how="left",
    )
    out = merged.sort_values("rank").head(30).copy()
    out["date"] = out["date"].dt.strftime("%Y-%m-%d")
    for col in ["weight", "score", "trend", "breakout", "quality", "risk"]:
        out[col] = out[col].astype(float).round(4)
    out["rank"] = out["rank"].astype(int)
    return out[
        [
            "date",
            "order_book_id",
            "industry_name",
            "rank",
            "weight",
            "score",
            "trend",
            "breakout",
            "quality",
            "risk",
        ]
    ]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    SUBMIT.mkdir(parents=True, exist_ok=True)
    ranking = ranking_system_table()
    holdings = sample_holdings()
    for target in [OUT, SUBMIT]:
        ranking.to_csv(target / "ranking_system_table.csv", index=False, encoding="utf-8-sig")
        holdings.to_csv(target / "sample_holdings.csv", index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    main()

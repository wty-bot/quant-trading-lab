from __future__ import annotations

from pathlib import Path
import shutil
import textwrap

import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyBboxPatch
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "reports" / "final_strategy_assets"
SUBMIT_REPORT_ASSETS = ROOT / "final_submission_assets" / "report" / "final_strategy_assets"
SUBMIT_SCREENSHOTS = ROOT / "final_submission_assets" / "screenshots"
TABLES = ROOT / "results" / "tables"
BACKTESTS = ROOT / "results" / "final_backtests"


def _font() -> None:
    candidates = ["Microsoft YaHei", "SimHei", "SimSun", "Noto Sans CJK SC"]
    installed = {f.name for f in font_manager.fontManager.ttflist}
    for name in candidates:
        if name in installed:
            plt.rcParams["font.sans-serif"] = [name]
            break
    plt.rcParams["axes.unicode_minus"] = False


def _box(ax, xy, width, height, text, face="#f7f8fb", edge="#334155", size=10.5, weight="normal"):
    patch = FancyBboxPatch(
        xy,
        width,
        height,
        boxstyle="round,pad=0.02,rounding_size=0.025",
        linewidth=1.1,
        edgecolor=edge,
        facecolor=face,
    )
    ax.add_patch(patch)
    ax.text(
        xy[0] + width / 2,
        xy[1] + height / 2,
        text,
        ha="center",
        va="center",
        fontsize=size,
        fontweight=weight,
        linespacing=1.25,
    )


def _save(fig, name: str) -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    fig.savefig(ASSETS / name, dpi=220, bbox_inches="tight")
    plt.close(fig)


def ranking_tree() -> None:
    fig, ax = plt.subplots(figsize=(11.5, 6.4))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.text(0.5, 0.96, "排名系统分支与权重设置", ha="center", va="center", fontsize=17, fontweight="bold")

    _box(ax, (0.38, 0.78), 0.24, 0.11, "综合得分\nScore", face="#e0f2fe", edge="#0369a1", size=13, weight="bold")

    modules = [
        ("趋势 Trend\n45%", "63日动量\n126日动量\n252日动量\nMA60/MA120强度", 0.04, "#dcfce7", "#15803d"),
        ("突破 Breakout\n20%", "252日高点接近度\n20/60日成交额趋势", 0.29, "#fef3c7", "#b45309"),
        ("质量 Quality\n20%", "ROE、ROA\n毛利率\n经营现金流/债务", 0.54, "#ede9fe", "#6d28d9"),
        ("风险 Risk\n15%", "120日波动率\n120日下行波动率\n252日回撤", 0.79, "#fee2e2", "#b91c1c"),
    ]
    for title, body, x, face, edge in modules:
        _box(ax, (x, 0.54), 0.17, 0.13, title, face=face, edge=edge, size=11.5, weight="bold")
        _box(ax, (x - 0.01, 0.25), 0.19, 0.20, body, face="#ffffff", edge=edge, size=10.2)
        ax.annotate("", xy=(x + 0.085, 0.67), xytext=(0.50, 0.78), arrowprops={"arrowstyle": "-|>", "lw": 1.1, "color": edge})
        ax.annotate("", xy=(x + 0.085, 0.45), xytext=(x + 0.085, 0.54), arrowprops={"arrowstyle": "-|>", "lw": 1.0, "color": edge})

    ax.text(
        0.5,
        0.12,
        "处理流程：股票池过滤 → 子因子计算 → 横截面去极值 → z-score 标准化 → 模块得分 → 综合排名 → 取前 30 名进入组合",
        ha="center",
        va="center",
        fontsize=10.5,
    )
    _save(fig, "ranking_tree.png")


def ranking_functions() -> None:
    rows = [
        ["趋势", "动量", "MOM_N = close(0) / close(-N) - 1，N=63/126/252", "越高越好"],
        ["趋势", "均线强度", "MA_strength = 0.5*close/MA60 + 0.5*close/MA120", "越高越好"],
        ["突破", "高点接近度", "HighProx = close(0) / max(close, 252日)", "越高越好"],
        ["突破", "成交活跃度", "VolumeTrend = AvgAmount(20) / AvgAmount(60)", "越高越好"],
        ["质量", "盈利能力", "Quality_1 = z(ROE) + z(ROA)", "越高越好"],
        ["质量", "利润质量", "Quality_2 = z(毛利率) + z(经营现金流/债务)", "越高越好"],
        ["风险", "价格波动", "Vol120 = std(日收益率, 120日)", "越低越好"],
        ["风险", "下行风险", "DownVol120 = std(min(日收益率,0), 120日)", "越低越好"],
        ["风险", "阶段回撤", "DD252 = close(0) / max(close, 252日) - 1", "回撤越小越好"],
    ]
    fig, ax = plt.subplots(figsize=(12, 5.9))
    ax.axis("off")
    ax.text(0.5, 0.98, "排名系统函数与方向", ha="center", va="top", fontsize=17, fontweight="bold")
    table = ax.table(
        cellText=rows,
        colLabels=["模块", "函数/子因子", "公式或定义", "排序方向"],
        cellLoc="center",
        colLoc="center",
        colWidths=[0.12, 0.18, 0.52, 0.16],
        loc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9.8)
    table.scale(1, 1.55)
    for (r, c), cell in table.get_celld().items():
        cell.set_edgecolor("#94a3b8")
        if r == 0:
            cell.set_facecolor("#e2e8f0")
            cell.set_text_props(weight="bold")
        elif r % 2 == 0:
            cell.set_facecolor("#f8fafc")
    _save(fig, "ranking_functions.png")


def standardized_parameters() -> None:
    rows = [
        ("组合方向", "纯多头组合；不做杠杆、不做空。"),
        ("持仓数量", "固定持有 30 只；全区间未低于 25 只。"),
        ("价格过滤", "保留 close(0) > 2 的低价股剔除思想，A 股口径为收盘价 > 2 元。"),
        ("流动性过滤", "以 20 日平均成交额 > 3000 万元替代美股成交量口径。"),
        ("市值过滤", "以总市值 > 30 亿元作为人民币市值口径。"),
        ("初始资金", "初始资金为 100 万资金单位，净值按资金单位归一。"),
        ("交易成本", "交易成本按 15 bps 比例成本计入组合净值。"),
        ("回测区间", "Max：2005-01-31 至 2026-06-16。\n最近 5 年：2021-06-30 至 2026-06-16。"),
    ]
    fig, ax = plt.subplots(figsize=(11.8, 8.2))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.text(0.5, 0.96, "标准化参数与 A 股等价实现", ha="center", va="center", fontsize=17, fontweight="bold")
    ax.text(
        0.5,
        0.90,
        "本项目保留课程标准化参数的约束思想，并根据 A 股数据字段和交易制度转换为可执行口径。",
        ha="center",
        va="center",
        fontsize=10.5,
    )
    for i, (name, desc) in enumerate(rows):
        row, col = divmod(i, 2)
        x = 0.07 + col * 0.47
        y = 0.76 - row * 0.16
        _box(ax, (x, y), 0.39, 0.105, f"{name}\n{desc}", face="#f8fafc", edge="#475569", size=8.8, weight="normal")
    _save(fig, "standardized_parameter_mapping.png")


def simulation_settings() -> None:
    cards = [
        ("股票池过滤", "A 股普通股\n剔除 ST / 停牌 / 金融\n上市满 273 个交易日\nclose > 2\n20日平均成交额 > 3000万\n总市值 > 30亿"),
        ("排名与买入", "趋势45% + 突破20%\n质量20% + 风险15%\n每季度调仓\n买入综合排名前30名"),
        ("卖出与持有", "原持仓仍在前60名则保留\n跌出前60名或不满足股票池则卖出\n停牌不假设立即成交\n复牌后重新检查"),
        ("权重与仓位", "逆波动率权重\n保留约2%现金\n中证800 MA240市场过滤\n8%目标波动率控制"),
        ("成本与基准", "初始资金100万资金单位\n交易成本15 bps计入净值\n基准：中证800\n报告5Y与Max结果"),
    ]
    fig, ax = plt.subplots(figsize=(12, 6.5))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.text(0.5, 0.96, "模拟交易系统设置总览", ha="center", va="center", fontsize=17, fontweight="bold")
    xs = [0.05, 0.385, 0.72, 0.215, 0.555]
    ys = [0.58, 0.58, 0.58, 0.18, 0.18]
    for (title, body), x, y in zip(cards, xs, ys):
        _box(ax, (x, y), 0.23, 0.28, f"{title}\n\n{body}", face="#ffffff", edge="#475569", size=10.5, weight="normal")
    _save(fig, "simulation_settings.png")


def _summary(label: str) -> pd.Series:
    raw = pd.read_csv(BACKTESTS / label / "summary.csv", index_col=0, header=None).squeeze("columns")
    return raw


def backtest_summary_panel(label: str, title: str) -> None:
    s = _summary(label)
    metrics = [
        ("年化收益", f"{float(s['annual_return']):.2%}"),
        ("累计收益", f"{float(s['cumulative_return']):.2%}"),
        ("最大回撤", f"{float(s['max_drawdown']):.2%}"),
        ("Sharpe", f"{float(s['sharpe']):.4f}"),
        ("Sortino", f"{float(s['sortino']):.4f}"),
        ("信息比率", f"{float(s['information_ratio']):.4f}"),
        ("年化换手率", f"{float(s['annual_turnover']):.2f}"),
        ("最终净值", f"{float(s['final_nav']):.4f}"),
        ("基准最终净值", f"{float(s['benchmark_final_nav']):.4f}"),
    ]
    fig, ax = plt.subplots(figsize=(10.5, 5.8))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.text(0.5, 0.94, title, ha="center", va="center", fontsize=17, fontweight="bold")
    ax.text(0.5, 0.86, f"回测区间：{s['start_date']} 至 {s['end_date']}    基准：中证800", ha="center", fontsize=10.8)
    for i, (name, value) in enumerate(metrics):
        row, col = divmod(i, 3)
        x = 0.07 + col * 0.31
        y = 0.61 - row * 0.19
        _box(ax, (x, y), 0.25, 0.12, f"{name}\n{value}", face="#f8fafc", edge="#334155", size=12, weight="bold")
    _save(fig, f"backtest_summary_{label}.png")


def holding_allocation() -> None:
    holdings = pd.read_csv(TABLES / "sample_holdings.csv")
    top = holdings.sort_values("weight", ascending=False).head(10)
    industry = holdings.groupby("industry_name")["weight"].sum().sort_values(ascending=False).head(8)

    fig, axes = plt.subplots(2, 1, figsize=(11.5, 9.2))
    fig.suptitle("样例调仓日持仓分配", fontsize=17, fontweight="bold")

    axes[0].barh(top["order_book_id"][::-1], top["weight"][::-1], color="#2563eb")
    axes[0].set_title("前十大个股权重")
    axes[0].set_xlabel("组合权重")
    axes[0].grid(True, axis="x", alpha=0.25)
    axes[0].tick_params(axis="y", labelsize=9)

    labels = [textwrap.shorten(str(x), width=16, placeholder="...") for x in industry.index]
    axes[1].barh(labels[::-1], industry.values[::-1], color="#16a34a")
    axes[1].set_title("前八大行业权重")
    axes[1].set_xlabel("组合权重")
    axes[1].grid(True, axis="x", alpha=0.25)
    axes[1].tick_params(axis="y", labelsize=8.5)
    fig.tight_layout(rect=[0, 0, 1, 0.94], h_pad=2.2)
    _save(fig, "holding_allocation.png")


def copy_to_submission() -> None:
    for target in [SUBMIT_REPORT_ASSETS, SUBMIT_SCREENSHOTS]:
        target.mkdir(parents=True, exist_ok=True)
        for image in ASSETS.glob("*.png"):
            shutil.copy2(image, target / image.name)


def main() -> None:
    _font()
    ranking_tree()
    ranking_functions()
    standardized_parameters()
    simulation_settings()
    backtest_summary_panel("5y", "最近 5 年模拟交易总结")
    backtest_summary_panel("max", "Max 模拟交易总结")
    holding_allocation()
    copy_to_submission()


if __name__ == "__main__":
    main()

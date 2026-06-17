# A 股多因子量化交易系统

本仓库为《基本面量化交易》期末小组项目提交版，包含一套面向 A 股市场的多因子纯多头量化交易系统。项目内容覆盖排名系统、模拟交易规则、最近 5 年与 Max 回测、敏感性测试、持仓与交易过程分析、最终课程报告以及复现实验所需的数据与代码。

## 项目产物

- [最终 Word 报告](final_submission_assets/report/A股多因子量化交易系统课程报告.docx)
- [最终 Markdown 报告](final_submission_assets/report/A股多因子量化交易系统课程报告.md)
- [报告图表与截图](final_submission_assets/report/final_strategy_assets)
- [提交用截图目录](final_submission_assets/screenshots)
- [核心结果表](final_submission_assets/result_tables)
- [原始回测数据集](data/backtest_dataset)
- [策略实现](src/strategy/trend_quality_core.py)
- [数据加载模块](src/data/local_loader.py)
- [回测结果明细](results/final_backtests)
- [汇总图表和诊断表](results)

## 策略概览

策略为 A 股纯多头组合，不做杠杆、不做空。每个调仓日先进行可交易性过滤，再使用趋势、突破、质量和风险四类模块构建综合排名，持有排名靠前的 30 只股票。组合采用季度调仓、60 名卖出缓冲、逆波动率权重、中证 800 MA240 市场过滤和 8%目标波动率控制。

核心设置：

- 股票池：A 股普通股，剔除 ST、停牌、金融行业、上市时间不足、价格过低、成交额不足和市值过小的股票。
- 排名系统：趋势 45%、突破 20%、质量 20%、风险 15%。
- 持仓数量：固定 30 只，全回测区间未低于 25 只。
- 调仓频率：季度调仓。
- 权重方式：逆波动率权重。
- 风险控制：市场过滤、目标波动率、个股回撤分数惩罚。
- 基准：中证 800。

## 核心结果

| 区间 | 年化收益 | 累计收益 | 最大回撤 | Sharpe | Sortino | 年化换手率 | 最终净值 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 最近 5 年 | 10.74% | 62.64% | -7.30% | 1.2014 | 1.3036 | 13.45 | 1.6264 |
| Max | 7.49% | 342.26% | -16.20% | 0.9206 | 0.9560 | 9.89 | 4.4226 |

Max 区间 Sharpe 未超过 1，报告中已将其作为局限性披露。策略长样本更偏防守型，优势主要体现在回撤控制和风险预算。

## 目录结构

```text
data/backtest_dataset/
  米筐账号下载整理的 A 股历史数据，包含行情、指数、基础信息、状态、财务因子、复权、分红和无风险利率。

final_submission_assets/
  report/                  最终课程报告及报告内嵌图表
  screenshots/             排名系统、模拟交易设置、持仓分配、绩效统计、净值、回撤、年度收益图
  result_tables/           最终绩效、排名系统、样例持仓、敏感性测试、换手成本等表格

results/
  final_backtests/         最近 5 年和 Max 回测明细
  figures/                 净值、回撤、年度收益图
  tables/                  绩效、持仓、敏感性、行业暴露、市值暴露等汇总表

src/
  data/                    本地静态数据加载模块
  strategy/                最终策略实现
  analysis/                图表、支撑材料、结果表和 Word 报告生成脚本

tests/
  数据加载模块测试
```

## 支撑材料

报告中已嵌入以下关键支撑材料：

- 标准化参数与 A 股等价实现：`final_submission_assets/screenshots/standardized_parameter_mapping.png`
- 排名系统分支与权重：`final_submission_assets/screenshots/ranking_tree.png`
- 排名函数与方向：`final_submission_assets/screenshots/ranking_functions.png`
- 模拟交易系统设置：`final_submission_assets/screenshots/simulation_settings.png`
- 样例调仓日持仓分配：`final_submission_assets/screenshots/holding_allocation.png`
- 最近 5 年模拟交易总结：`final_submission_assets/screenshots/backtest_summary_5y.png`
- Max 模拟交易总结：`final_submission_assets/screenshots/backtest_summary_max.png`

## 数据说明

`data/backtest_dataset` 已包含项目使用的原始静态数据。数据文件较大，仓库使用 Git LFS 管理 `.h5`、`.pkl` 和 `.npy` 文件。克隆仓库后如需取得完整数据，请确保本机已安装 Git LFS，并执行：

```bash
git lfs pull
```

数据构成包括：

- 股票日线行情：`stocks.h5`
- 指数日线行情：`indexes.h5`
- 历史 A 股基础信息：`all_instruments_monthly_full_history.pkl`
- 财务与估值因子：`factor_monthly_full_history.pkl`
- ST / 停牌状态：`aux_status_*.pkl`
- 分红、拆股 / 送转、复权因子
- 无风险利率
- 调仓日期和交易日历
- 数据清单：`manifest.json`

## 复现方式

建议使用 Python 3.11 环境，并安装项目所需依赖。进入仓库根目录后可运行：

```bash
python -m pytest tests -q
python src/analysis/generate_report_tables.py
python src/analysis/generate_support_materials.py
python src/analysis/export_report_docx.py
```

项目默认从仓库内的 `data/backtest_dataset` 读取静态数据，不需要在回测阶段访问在线接口。如需使用其他数据目录，可设置环境变量 `RQ_BACKTEST_DATASET_DIR` 指向对应路径。

## 主要文件

- 策略代码：[src/strategy/trend_quality_core.py](src/strategy/trend_quality_core.py)
- 数据加载：[src/data/local_loader.py](src/data/local_loader.py)
- 5 年回测摘要：[results/final_backtests/5y/summary.csv](results/final_backtests/5y/summary.csv)
- Max 回测摘要：[results/final_backtests/max/summary.csv](results/final_backtests/max/summary.csv)
- 敏感性测试：[results/tables/sensitivity_summary.csv](results/tables/sensitivity_summary.csv)
- 排名系统表：[results/tables/ranking_system_table.csv](results/tables/ranking_system_table.csv)
- 样例持仓：[results/tables/sample_holdings.csv](results/tables/sample_holdings.csv)

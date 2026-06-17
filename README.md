# A 股多因子量化交易系统课程项目

本仓库是《基本面量化交易》期末小组项目的最终提交版。项目目标是设计一套可在米筐数据环境中实现的 A 股多因子量化交易系统，并完成排名系统、模拟交易规则、最近 5 年与 Max 回测、敏感性测试、风险暴露分析和最终报告。

## 最终策略

策略为 A 股纯多头多因子组合，核心思想是用趋势和突破捕捉中期强势，用质量因子约束基本面风险，用低波和回撤信号控制组合风险。

主要设置：

- 股票池：A 股普通股，剔除 ST、停牌、金融行业，保留满足价格、市值和流动性约束的股票。
- 排名模块：趋势、突破、质量、风险。
- 持仓数量：30 只，满足课程要求的至少 25 只多头持仓。
- 调仓频率：季度调仓。
- 权重：逆波动率权重。
- 风控：中证 800 MA240 市场过滤，组合 8%目标波动率，个股回撤分数惩罚。

## 核心结果

| 区间 | 年化收益 | 累计收益 | 最大回撤 | Sharpe | Sortino | 年化换手率 | 最终净值 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 最近 5 年 | 10.74% | 62.64% | -7.30% | 1.2014 | 1.3036 | 13.45 | 1.6264 |
| Max | 7.49% | 342.26% | -16.20% | 0.9206 | 0.9560 | 9.89 | 4.4226 |

## 目录说明

```text
final_submission_assets/
  report/                  最终课程报告 Markdown 和 Word 版本
  screenshots/             净值、回撤、年度收益图
  result_tables/           核心结果表、敏感性测试表、持仓数证明

results/
  final_backtests/         最近 5 年和 Max 回测明细
  figures/                 报告图表副本
  tables/                  汇总表、因子相关、市值暴露、行业暴露

src/
  data/                    本地数据加载模块
  strategy/                最终策略实现
  analysis/                图表、敏感性和报告导出脚本

tests/                     数据加载模块测试
reports/final_report.md    报告源文件
EXPERIMENTS.md             实验记录
FINAL_ACCEPTANCE_AUDIT.md  四项评分标准验收审计
```

## 关键文件

- 最终报告：`final_submission_assets/report/A股多因子量化交易系统课程报告.docx`
- Markdown 报告：`final_submission_assets/report/A股多因子量化交易系统课程报告.md`
- 最终策略代码：`src/strategy/trend_quality_core.py`
- 数据加载代码：`src/data/local_loader.py`
- 5 年结果：`results/final_backtests/5y/summary.csv`
- Max 结果：`results/final_backtests/max/summary.csv`
- 敏感性测试：`results/tables/sensitivity_summary.csv`
- 验收审计：`FINAL_ACCEPTANCE_AUDIT.md`

## 复现说明

项目依赖米筐账号下载并整理的 A 股静态数据。默认数据目录为：

```text
D:\RiceQuantData\backtest_dataset
```

在已配置 Python 环境中运行：

```powershell
D:\Miniconda3\envs\ricequant-final\python.exe -m pytest tests -q
D:\Miniconda3\envs\ricequant-final\python.exe src\analysis\generate_final_assets.py
D:\Miniconda3\envs\ricequant-final\python.exe src\analysis\generate_sensitivity_summary.py
```

说明：本仓库保留最终结果文件和图表，未提交本地米筐原始数据缓存。

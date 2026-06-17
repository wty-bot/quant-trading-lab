# 项目结构

本仓库为课程项目公开提交版，目录按“报告、结果、代码、审计”组织。

```text
final_submission_assets/
  report/
    A股多因子量化交易系统课程报告.docx
    A股多因子量化交易系统课程报告.md
  screenshots/
    nav_5y.png
    nav_max.png
    drawdown_5y.png
    drawdown_max.png
    yearly_return_5y.png
    yearly_return_max.png
  result_tables/
    final_summary_table.csv
    sensitivity_summary.csv
    holding_count_summary.csv
    turnover_cost_summary.csv

results/
  final_backtests/
    5y/
    max/
  figures/
  tables/

src/
  data/local_loader.py
  strategy/trend_quality_core.py
  analysis/

tests/
  test_local_loader.py

reports/
  final_report.md

EXPERIMENTS.md
FINAL_ACCEPTANCE_AUDIT.md
README.md
```

本仓库不提交米筐原始数据缓存。复现时需要本地存在 `D:\RiceQuantData\backtest_dataset`。

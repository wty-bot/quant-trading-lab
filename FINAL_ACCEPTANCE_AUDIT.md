# 最终验收审计

更新时间：2026-06-17

审计对象：A 股趋势质量低波风险预算多因子策略。

最终结果目录：

- 最近 5 年：`reports/local_backtests/final_enhanced_ma240_tv08_5y`
- Max：`reports/local_backtests/final_enhanced_ma240_tv08_max`

最终报告：

- `reports/final_report.md`

证据资产：

- `reports/final_strategy_assets`

## 1. 标准化参数一致性

结论：通过。

证据：

- 原始作业要求已在 `EXPERIMENTS.md` 第 0 节复核。
- 策略持仓数不少于 25：`reports/final_strategy_assets/holding_count_summary.csv`
- 最近 5 年持仓数：最小 30，中位数 30，最大 30，低于 25 的交易日为 0。
- Max 持仓数：最小 30，中位数 30，最大 30，低于 25 的交易日为 0。
- 最近 5 年与 Max 回测均完成：`reports/final_strategy_assets/final_summary_table.csv`
- 价格、市值、流动性、ST、停牌、上市时间、行业过滤逻辑：`src/strategy/trend_quality_core.py`
- 本地数据加载：`src/data/local_loader.py`

说明：

- 作业原始参数以美股为背景。本项目使用 A 股数据，因此市值和成交量过滤采用人民币口径等价转换。
- 策略没有声称使用米筐网页端模拟交易页面。

## 2. 合理性

结论：通过。

证据：

- 策略设计说明：`reports/final_report.md`
- 实验记录：`EXPERIMENTS.md`
- 因子相关矩阵：`reports/final_strategy_assets/factor_correlation_5y.csv`
- 因子相关矩阵：`reports/final_strategy_assets/factor_correlation_max.csv`
- 市值暴露诊断：`reports/final_strategy_assets/module_market_cap_correlation_5y.csv`
- 市值暴露诊断：`reports/final_strategy_assets/module_market_cap_correlation_max.csv`

核对：

- 每个因子模块均有经济逻辑：趋势、突破、质量、风险。
- 核心参数有解释：季度调仓降低噪音交易，MA240 捕捉长周期市场环境，8%目标波动控制尾部风险，30 只持仓满足分散度和作业要求。
- 局限性已写入报告第九节，包括 Max Sharpe 未超过 1、强牛市可能跑输、趋势与突破相关性较高、金融行业未覆盖、交易成本较高。
- 代码逻辑与文档一致，最终策略实现位于 `src/strategy/trend_quality_core.py`。

## 3. 完整性

结论：基本通过。

证据：

- 本地数据加载模块：`src/data/local_loader.py`
- 数据加载测试：`tests/test_local_loader.py`
- 最终策略模块：`src/strategy/trend_quality_core.py`
- 最近 5 年结果：`reports/local_backtests/final_enhanced_ma240_tv08_5y`
- Max 结果：`reports/local_backtests/final_enhanced_ma240_tv08_max`
- 图表与表格：`reports/final_strategy_assets`
- 最终报告：`reports/final_report.md`
- 实验记录：`EXPERIMENTS.md`

已完成项目：

- 本地静态数据读取。
- 策略可运行。
- 最近 5 年回测。
- Max 回测。
- 敏感性测试：目标波动率、市场过滤均线长度、调仓频率、卖出缓冲。
- 持仓数证明。
- 因子相关、行业暴露、市值暴露、换手与成本分析。

尚需注意：

- 当前交付为 Markdown 报告和本地图表资产；若需要 Word/PDF，可基于 `reports/final_report.md` 转换。

## 4. 有效性

结论：通过，但不是完美策略。

证据：

- 总结指标：`reports/final_strategy_assets/final_summary_table.csv`
- 净值图：`reports/final_strategy_assets/nav_5y.png`
- 净值图：`reports/final_strategy_assets/nav_max.png`
- 回撤图：`reports/final_strategy_assets/drawdown_5y.png`
- 回撤图：`reports/final_strategy_assets/drawdown_max.png`
- 年度收益：`reports/final_strategy_assets/yearly_return_5y.csv`
- 年度收益：`reports/final_strategy_assets/yearly_return_max.csv`
- 换手成本：`reports/final_strategy_assets/turnover_cost_summary.csv`

最近 5 年：

- 年化收益：10.74%
- 最大回撤：-7.30%
- Sharpe：1.2014
- Sortino：1.3036
- 最终净值：1.6264

Max：

- 年化收益：7.49%
- 最大回撤：-16.20%
- Sharpe：0.9206
- Sortino：0.9560
- 最终净值：4.4226

判断：

- 最近 5 年表现达到较好的风险调整收益。
- Max 的回撤控制较好，但 Sharpe 未超过 1，且最终净值低于基准；这已在报告中如实披露。
- 交易成本后净值、换手率和成本拖累均已记录。

## 5. 创造性

结论：通过。

证据：

- 策略结构说明：`reports/final_report.md`
- 敏感性测试汇总：`reports/final_strategy_assets/sensitivity_summary.csv`
- 敏感性透视表：`reports/final_strategy_assets/sensitivity_pivot.csv`
- 实验记录：`EXPERIMENTS.md`

核对：

- 策略不只使用传统基本面因子，还引入趋势、突破、下行风险、目标波动率和市场状态过滤。
- 有明确经济动机的增强版本：季度调仓、MA240、8%目标波动、逆波动率权重、个股回撤分数惩罚。
- 保留负面/中性结果：卖出缓冲 90 名表现变差，未采用；高目标波动率提高短期收益但损害 Max 回撤和 Sharpe，未采用。
- 讨论了 A 股特异性处理：ST/停牌、金融行业剔除、人民币口径市值与成交额过滤、长周期市场状态过滤。

## 6. 最终审计结论

四项评分标准审计结果：

- 合理性：通过。
- 完整性：基本通过。
- 有效性：通过，但 Max Sharpe 未超过 1，需作为局限披露。
- 创造性：通过。

本项目可以进入最终提交资产整理阶段。不得宣称 Max 区间 Sharpe 超过 1，也不得声称使用米筐网页端模拟交易页面。

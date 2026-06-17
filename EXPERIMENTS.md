# 实验记录与审计日志

更新时间：2026-06-17

本文件只记录最终提交口径会使用的实验和证据。早期废弃候选策略不进入正式叙事、正文或附录。

## 0. 原始作业要求复核

依据 `期末小组项目.pdf`，作业要求是设计一个可在米筐或 P123 平台实现的量化交易系统，包括排名算法和模拟交易规则。

标准化参数约束：

- 多头头寸至少包含 25 个具有一定流动性的持仓。
- 市值、价格和流动性过滤需体现：`Mktcap > 200`、`close(0) > 2`、`Avgdailytot(20) > 200000`。本项目使用 A 股环境，采用人民币口径等价过滤。
- 初始资金为 100 万，滑点和交易成本需在回测中体现。
- 必须报告最近 5 年和 Max 两个区间。
- 可以放宽部分参数进一步测试，但必须说明理由。

本项目最终主策略不与上述标准化参数冲突：固定持有 30 只股票，使用价格、市值、流动性、ST、停牌、上市时间和行业可比性过滤，并输出最近 5 年与 Max 结果。

## 1. 数据与环境验证

数据源为本地静态缓存目录：

```text
D:\RiceQuantData\backtest_dataset
```

核心事实：

- `manifest.json` 已存在并完成 SHA256 校验。
- 已缓存股票日线、指数日线、交易日历、历史基础信息、ST/停牌、财务/估值因子、分红、复权因子、无风险利率。
- 行业字段存在于历史基础信息快照中，可用于剔除金融行业和行业暴露分析。
- 正式研究回测不动态调用 `rqdatac.get_factor` 或 `rqdatac.get_price`。

代码证据：

- 数据加载模块：`src/data/local_loader.py`
- 策略模块：`src/strategy/trend_quality_core.py`
- 最终资产生成脚本：`src/analysis/generate_final_assets.py`
- 敏感性汇总脚本：`src/analysis/generate_sensitivity_summary.py`

## 2. 最终主策略设定

策略名称：趋势质量低波风险预算多因子策略。

股票池：

- A 股普通股。
- 剔除 ST / *ST。
- 剔除停牌。
- 剔除金融行业。
- 上市满 273 个交易日。
- `close > 2`。
- 20 日平均成交额满足流动性阈值。
- 市值满足 A 股人民币口径阈值。

排名因子：

- 趋势：63 / 126 / 252 日动量、60 / 120 日均线相对强度。
- 突破：接近 252 日高点程度、20 日相对 60 日成交额趋势。
- 质量：ROE、ROA、毛利率、经营现金流/债务。
- 风险：120 日波动率、120 日下行波动率、252 日回撤。

交易与风控：

- 季度调仓。
- 持有综合得分前 30 只股票。
- 卖出缓冲阈值 60 名。
- 逆波动率权重。
- 中证 800 指数 MA240 市场过滤。
- 组合目标波动率 8%。
- 个股 252 日回撤低于 -25% 时在排名中施加分数惩罚，而不是日内强制清仓，保证组合分散度。
- 现金部分按本地无风险利率缓存计入低风险收益。

最终结果目录：

- 最近 5 年：`reports/local_backtests/final_enhanced_ma240_tv08_5y`
- Max：`reports/local_backtests/final_enhanced_ma240_tv08_max`

## 3. 最终主策略结果

最近 5 年，`2021-06-30` 至 `2026-06-16`：

- 年化收益：10.74%
- 累计收益：62.64%
- 最大回撤：-7.30%
- Sharpe：1.2014
- Sortino：1.3036
- 信息比率：0.5378
- Beta：0.2097
- 年化换手率：13.45
- 交易成本拖累：9.63%
- 最终净值：1.6264
- 持仓数：最小 30，中位数 30，最大 30，低于 25 的交易日为 0

Max，`2005-01-31` 至 `2026-06-16`：

- 年化收益：7.49%
- 累计收益：342.26%
- 最大回撤：-16.20%
- Sharpe：0.9206
- Sortino：0.9560
- 信息比率：-0.1868
- Beta：0.1494
- 年化换手率：9.89
- 交易成本拖累：30.55%
- 最终净值：4.4226
- 持仓数：最小 30，中位数 30，最大 30，低于 25 的交易日为 0

证据文件：

- `reports/final_strategy_assets/final_summary_table.csv`
- `reports/final_strategy_assets/holding_count_summary.csv`
- `reports/final_strategy_assets/turnover_cost_summary.csv`
- `reports/final_strategy_assets/nav_5y.png`
- `reports/final_strategy_assets/nav_max.png`
- `reports/final_strategy_assets/drawdown_5y.png`
- `reports/final_strategy_assets/drawdown_max.png`

## 4. 结构优化记录

### 4.1 季度调仓

动机：

- 因子快照为月度，但趋势与质量类信号的经济含义并不要求高频交易。
- 月度交易容易被短期排名噪音驱动，增加换手和成本。

结果：

- 季度调仓显著降低换手，并改善近 5 年 Sharpe 与 Max 回撤。
- 该调整保留为最终主策略结构。

证据：

- `reports/local_backtests/structural_turnover_test/quarterly_5y`
- `reports/local_backtests/structural_turnover_test/quarterly_max`

### 4.2 卖出缓冲 90 名

动机：

- 测试更宽的缓冲是否进一步降低换手。

结果：

- 5 年和 Max 表现均弱于最终候选。
- 结论是缓冲过宽会保留过多已经失效的持仓，降低组合更新效率。
- 不采用。

证据：

- `reports/local_backtests/structural_turnover_test/sell90_5y`
- `reports/local_backtests/structural_turnover_test/sell90_max`

### 4.3 目标波动率

动机：

- A 股长样本中熊市与震荡市占比高，单纯追求高仓位会放大回撤。
- 目标波动率控制可以在高波动阶段自动降低风险暴露。

测试范围：

- 8%、10%、12%、14%、16%、18%、20%。

结论：

- 高目标波动率提高近 5 年收益，但 Max 回撤明显扩大，长期 Sharpe 下降。
- 8%目标波动率在 Max 回撤和 Sharpe 上更稳健，且近 5 年 Sharpe 仍大于 1。
- 最终采用 8%。

证据：

- `reports/final_strategy_assets/sensitivity_summary.csv`
- `reports/final_strategy_assets/sensitivity_pivot.csv`

### 4.4 市场过滤 MA 长度

动机：

- A 股指数趋势具有明显的长周期特征，过短均线容易被震荡反复打断。
- 使用长均线过滤意在避开大级别下行阶段，而不是做高频择时。

测试范围：

- MA120、MA150、MA180、MA200、MA240、MA300。

结论：

- MA240 在 Max Sharpe、Max 回撤与近 5 年表现之间取得较好平衡。
- MA300 回撤略低但 Max 收益与 Sharpe 不如 MA240。
- 最终采用 MA240。

证据：

- `reports/final_strategy_assets/sensitivity_summary.csv`
- `reports/final_strategy_assets/sensitivity_pivot.csv`

## 5. 风险暴露与归因诊断

已生成以下诊断文件：

- 因子相关矩阵：`reports/final_strategy_assets/factor_correlation_5y.csv`
- 因子相关矩阵：`reports/final_strategy_assets/factor_correlation_max.csv`
- 因子与市值相关：`reports/final_strategy_assets/module_market_cap_correlation_5y.csv`
- 因子与市值相关：`reports/final_strategy_assets/module_market_cap_correlation_max.csv`
- 行业暴露：`reports/final_strategy_assets/industry_exposure_rebalance_5y.csv`
- 行业暴露：`reports/final_strategy_assets/industry_exposure_rebalance_max.csv`
- 年度收益：`reports/final_strategy_assets/yearly_return_5y.csv`
- 年度收益：`reports/final_strategy_assets/yearly_return_max.csv`

主要解释：

- 近 5 年策略收益来自趋势、突破与风险预算共同作用；Beta 较低，说明结果不是简单指数暴露。
- Max 信息比率为负，说明长期仍未稳定跑赢中证 800，但回撤控制明显优于指数。
- 总体更像低回撤绝对收益型多因子策略，而非高 Beta 指数增强策略。

## 6. 已知局限

- Max Sharpe 为 0.9206，尚未超过 1；但 Max 回撤控制较好。
- 交易成本拖累在 Max 中达到 30.55%，说明换手仍然是重要成本来源。
- 市场过滤和目标波动率会降低牛市进攻性，导致强牛市可能跑输基准。
- 行业分类虽可用，但金融行业被整体剔除；金融行业内部的专门因子模型不在本项目范围内。
- 回测使用本地静态研究回测器生成结果，未声称使用网页端模拟交易页面。

## 7. 下一步交付

- 基于上述证据生成最终中文报告。
- 生成最终验收审计文件，逐条对应合理性、完整性、有效性、创造性。
- 整理截图和图表资产到最终提交目录。

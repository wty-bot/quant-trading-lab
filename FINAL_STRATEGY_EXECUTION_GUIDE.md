# 米筐 A 股量化交易系统终版策略设置与执行文档

更新时间：2026-06-16

## 1. 当前结论

本项目采用米筐 RQSDK / RQData / RQAlpha Plus 做 A 股基本面量化交易系统。当前已经把回测所需核心数据静态缓存到本地，后续正式策略不需要动态调用 RQData。

核心路线：

- 标的：A 股普通股票。
- 回测区间：Max 使用 `2005-01-31` 至 `2026-06-16`；近 5 年使用 `2021-06-30` 至 `2026-06-16`。
- 调仓频率：月度，使用缓存中记录的月末调仓日；因子快照、基础信息快照、ST/停牌快照与调仓日一一对应。
- 策略方向：质量 + 价值 + 动量 + 风险惩罚的多因子纯多头组合。
- 持仓数量：主版本持有 30 只股票；敏感性测试使用 25 / 50 只。
- 基准：`000906.XSHG` 中证 800。
- 初始资金：人民币口径建议使用 1,000,000；若报告要对齐原作业美元参数，说明本项目转为 A 股后使用同等名义本金。
- 交易成本：滑点 0.5%；佣金按米筐可配置项设定，若不能完全复刻“每笔 8 美元”，报告中说明 A 股环境下使用平台支持的固定/比例佣金替代。

## 2. 数据状态

正式回测数据目录：

```text
D:\RiceQuantData\backtest_dataset
D:\RiceQuantData\backtest_dataset\manifest.json
```

策略开发和回测应优先读取这个目录。该目录已经把分散在 bundle 和 project_cache 的正式数据复制到一起，并通过 `manifest.json` 记录用途、覆盖范围、源路径、文件大小和 SHA256 校验值。

原始数据来源目录：

```text
D:\RiceQuantData\bundle_sample\bundle\bundle
D:\RiceQuantData\project_cache
```

正式数据目录包含以下行情主干：

| 数据 | 覆盖范围 | 文件 |
|---|---|---|
| 股票日线价格、成交量、成交额 | `2005-01-04` 至 `2026-06-16`，5509 只 | `D:\RiceQuantData\backtest_dataset\stocks.h5` |
| 指数日线价格 | 已含 `000906.XSHG` | `D:\RiceQuantData\backtest_dataset\indexes.h5` |
| 交易日历 | 已有 | `D:\RiceQuantData\backtest_dataset\trading_dates.npy` |

正式数据目录还包含以下策略缓存：

| 数据 | 覆盖范围 | 文件 |
|---|---|---|
| 月度调仓日 | 259 个，`2005-01-31` 至 `2026-06-16` | `rebalance_dates_pre5y.csv`、`rebalance_dates_5y.csv` |
| 历史 A 股基础信息快照 | 259 个调仓日，796489 行 | `all_instruments_monthly_full_history.pkl` |
| ST / 停牌月度快照 | 259 个调仓日，全 A 股 | `aux_status_pre5y_full_a.pkl`、`aux_status_5y_full_a.pkl` |
| 财务/估值因子月度快照 | 259 个调仓日，796489 行 | `factor_monthly_full_history.pkl` |
| 分红 | `2005-01-04` 至 `2026-06-16` | `dividend_pre5y_all_a.pkl`、`dividend_5y_all_a.pkl` |
| 拆股/送转 | `2005-01-04` 至 `2026-06-16` | `split_pre5y_all_a.pkl`、`split_5y_all_a.pkl` |
| 复权因子 | `2005-01-04` 至 `2026-06-16` | `ex_factor_pre5y_all_a.pkl`、`ex_factor_5y_all_a.pkl` |
| 无风险利率 | `2005-01-04` 至 `2026-06-16` | `yield_curve_pre5y.pkl`、`yield_curve_5y.pkl` |

数据整理验证结果：

- `manifest.json` 共登记 20 个文件。
- 所有文件存在，SHA256 校验通过。
- `stocks.h5` 可读，含 5509 个股票键。
- `indexes.h5` 可读，确认包含 `000906.XSHG`。
- 因子、基础信息、ST/停牌缓存均可反序列化读取。

已缓存财务/估值因子：

```text
market_cap
pe_ratio_ttm
pb_ratio_ttm
book_to_market_ratio_ttm
return_on_equity_ttm
return_on_asset_ttm
gross_profit_margin_ttm
ocf_to_debt_ttm
```

## 3. 股票池与筛选规则

每个调仓日从全 A 股开始，使用本地缓存逐层筛选：

1. 基础身份过滤：
   - `type == CS`
   - `status == Active`
   - 已上市且未退市
   - 上市满 273 个交易日
2. 风险状态过滤：
   - 剔除 ST / *ST
   - 剔除当日停牌
3. 流动性过滤：
   - 当日收盘价 `close > 2`
   - 过去 20 个交易日平均成交额 `AvgDailyTurnover(20) > 20,000,000`
   - 至少有 250 个交易日价格历史，供动量和风险计算
4. 市值过滤：
   - `market_cap > 2,000,000,000`

说明：原作业的美股参数写作 `Mktcap > 200`、`close > 2`、`Avgdailytot(20) > 200000`。本项目转为 A 股后，价格阈值保留，市值和成交额使用人民币环境下更合理的等价过滤。

## 4. 排名系统

排名系统采用四个模块，先对每个因子横截面 winsorize，再 z-score 标准化。

质量 Quality，权重 35%：

- `return_on_equity_ttm`
- `return_on_asset_ttm`
- `gross_profit_margin_ttm`
- `ocf_to_debt_ttm`

价值 Value，权重 25%：

- `book_to_market_ratio_ttm`，越高越好
- `pe_ratio_ttm`，越低越好；负值剔除或置空

说明：`pb_ratio_ttm` 与 `book_to_market_ratio_ttm` 本质重复，不进入 baseline 价值模块。当 PE 因亏损或异常被置空时，价值模块会退化为 B/P 单因子，报告中需承认这一局限。

动量 Momentum，权重 25%：

- baseline 使用 12-1 月动量，即跳过最近 1 个月，计算前 12 个月收益。
- 公式为 `close[t-21] / close[t-252] - 1`。
- 若股票价格历史不足 273 个交易日，或 `t-252` 距上市首个交易日不足 60 个交易日，则动量置空。

风险 Risk，权重 15%：

- 使用本地价格计算过去 120 日收益率波动率。
- 波动率越低得分越高。

综合分：

```text
score = 0.35 * quality + 0.25 * value + 0.25 * momentum + 0.15 * low_risk
```

缺失值处理：

- 单个子因子缺失时，在同一模块内用可用子因子均值。
- 综合分缺失则不进入可买池。
- PE / PB 为负或极端异常时不参与价值分。

## 5. 交易规则与回测设置

主策略：

- 每月最后一个交易日调仓。
- 买入综合分最高的 30 只股票。
- 等权配置，目标仓位合计 98%，保留 2% 现金缓冲。
- 若持仓股票跌出前 60 名、变 ST、基础信息异常，则在可交易时卖出。
- 若持仓股票调仓日停牌，不发出卖出委托，保持原持仓；复牌后在下一次可交易调仓检查点重新排名，不合格则卖出。
- 不使用杠杆，不做空，不做行业或指数对冲。

敏感性测试：

| 测试项 | 参数 |
|---|---|
| 持仓数量 | 25 / 30 / 50 |
| 调仓频率 | 月度 / 双周 |
| 因子开关 | 去动量、去风险惩罚、仅质量价值 |
| 回测区间 | Max / 近 5 年 |

回测输出指标：

- 年化收益
- 累计收益
- Sharpe
- Sortino
- 最大回撤
- 换手率
- Alpha / Beta
- 信息比率
- 胜率
- 交易成本后收益

## 6. 执行步骤

环境：

```powershell
D:\Miniconda3\envs\ricequant-final\python.exe
D:\Miniconda3\envs\ricequant-final\Scripts\rqalpha-plus.exe
```

下一步代码工作：

0. 先写一个 RQAlpha Plus 文件 I/O 验证脚本，确认策略运行环境能读取 `D:\RiceQuantData\backtest_dataset\manifest.json`、`stocks.h5` 和核心 pickle 缓存。
1. 写一个本地数据加载模块，统一读取 `D:\RiceQuantData\backtest_dataset\manifest.json`，再根据 manifest 定位：
   - `stocks.h5`
   - `indexes.h5`
   - 历史基础信息快照
   - ST / 停牌缓存
   - 财务/估值因子缓存
2. 写正式策略文件，禁止在回测过程中调用 `rqdatac.get_factor`、`rqdatac.get_price` 等动态接口。
3. 先跑近 5 年，确认结果和交易日志正常。
4. 再跑 Max。
5. 导出回测报告、交易明细、持仓明细和绩效统计。

当前旧策略文件 `rq_qvmr_skeleton.py` 仍含动态 RQData 调用，只能作为逻辑参考，不能作为最终策略直接提交。

## 7. 作业产出怎么做

你最终需要提交的不是代码本身，而是一套“交易系统说明 + 截图 + 结果分析”。

权限口径必须写清楚：当前账号开通的是 RQSDK 教育版，包含 RQData 金融数据 API 与 RQAlpha Plus 基础回测功能，不是米筐网页端模拟交易页面。因此截图和结果证据应来自 RQAlpha Plus 本地回测输出、命令/配置截图、策略代码截图，以及用回测 CSV / pickle 生成的本地图表。

建议报告结构：

1. 摘要
   - 写清楚策略是 A 股多因子纯多头。
   - 简述核心思想：质量保证公司基本面，价值控制买入价格，动量捕捉趋势，低波动控制回撤。
2. 设计原则
   - 解释为什么选这些因子。
   - 说明数据完全静态缓存，避免回测中动态取数。
3. 排名系统
   - 展示四个模块及权重。
   - 解释每个因子的经济含义。
   - 附排名系统或代码截图。
4. 模拟交易设置
   - 股票池过滤规则。
   - 持仓数量、调仓频率、成本、滑点、基准。
   - 附 RQAlpha Plus 回测命令、配置文件或参数表截图。
5. 回测结果
   - 分别报告近 5 年和 Max。
   - 展示收益曲线、持仓分配、绩效统计、交易统计。
6. 稳健性测试
   - 比较 25 / 30 / 50 只。
   - 比较月度 / 双周。
   - 比较有无动量、有无风险惩罚。
7. 局限性
   - A 股版本与原美股参数不同。
   - 交易成本、停牌处理、财务数据滞后可能影响真实可交易性。

必备截图清单：

- 排名系统分支或因子代码截图。
- RQAlpha Plus 本地回测 summary 截图。
- RQAlpha Plus 回测命令、配置文件或参数表截图。
- 持仓分配图，来自 `stock_positions.csv` 或 `result.pkl`。
- 近 5 年绩效统计，来自 `summary.csv` / `report.xlsx` / `result.pkl`。
- Max 绩效统计，来自 `summary.csv` / `report.xlsx` / `result.pkl`。
- 净值曲线和回撤曲线，来自 `portfolio.csv` 或 `result.pkl`。
- 敏感性测试结果表，来自多组回测 summary 汇总。

作业原文提到“模拟交易总结页面、交易系统设置、持仓分配图表、交易表现统计数据”。在本项目中对应关系如下：

| 作业截图要求 | 本项目对应产物 |
|---|---|
| 模拟交易总结页面 | RQAlpha Plus `summary.csv` / `report.xlsx` / 本地 summary 图表 |
| 交易系统设置 | 回测命令、配置文件、参数表截图 |
| 持仓分配图表 | 由 `stock_positions.csv` 生成的持仓权重或行业分布图 |
| 交易表现统计数据 | `summary.csv`、`portfolio.csv`、`trades.csv`、本地绩效统计图 |

呈现形式：

- 主报告建议用 Word / PDF。
- 附录放参数表、因子说明、敏感性测试表。
- 不要声称使用了米筐网页模拟交易页面。
- 代码和缓存路径不需要全部放进正文，只在方法部分说明“使用米筐 RQSDK/RQAlpha Plus，本地静态缓存数据完成回测”。

## 8. 当前文件状态

保留：

- `FINAL_STRATEGY_EXECUTION_GUIDE.md`
- `rq_qvmr_skeleton.py`
- `rq_minimal_buy_hold.py`
- 作业 PDF 和 9 份多因子研报

归档：

- 旧调研报告、旧执行计划、旧美股支持验证等文档移动到 `output/old_docs`。

Git：

- 已初始化 Git。
- 已提交原始快照。
- 本文档完成后应再提交一次，作为终版执行文档版本。

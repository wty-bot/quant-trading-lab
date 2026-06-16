# 米筐 A 股量化交易系统实施规格书

用途：给后续 Codex 编写米筐策略代码、配置回测、整理结果和撰写报告使用。  
当前主线：米筐平台、A 股全市场、纯多头、中证 800 基准、QVM-R 多因子排名。

## 1. 项目目标

在米筐上实现一个 A 股多因子量化交易系统。系统必须包含：

- 股票池过滤；
- 排名算法；
- 买入、卖出、调仓、持仓权重规则；
- 交易成本和滑点设置；
- Max 与最近 5 年两组回测；
- 敏感性测试；
- 平台截图和本地结果整理。

最终报告不主动讨论从美股切到 A 股的合规问题，只呈现 A 股交易系统本身。

## 2. 米筐与 Agent 分工

| 环节 | 米筐上完成 | Agent 本地完成 |
|---|---|---|
| 数据验证 | 验证 A 股股票池、行情、财务、指数、行业字段 | 生成字段验证清单和替代方案 |
| 策略代码 | 粘贴、运行、调试策略 | 编写策略代码草稿和参数开关 |
| 因子研究 | 可选做 IC、分组收益、因子树截图 | 设计因子结构、权重、标准化和解释 |
| 回测配置 | 设置资金、基准、滑点、佣金、回测区间 | 提供配置表和检查清单 |
| 回测结果 | 生成绩效摘要、持仓、交易、图表 | 整理指标表、对比表、结论 |
| 截图 | 在平台页面截图 | 告诉你截哪里、检查截图是否齐全 |
| 报告 | 提供平台结果证据 | 写报告结构、文字、表格和复核清单 |

原则：回测结果和截图以米筐为准；本地 Agent 负责设计、代码、解释和整理，不在本地伪造平台结果。

## 3. A 股等价参数

| 参数 | 本项目设置 | 米筐实现思路 |
|---|---|---|
| 市场 | A 股全市场 | `all_instruments(type='CS', market='cn')` |
| 股票池 | 排除 ST、停牌、新股、低流动性股票 | 每个调仓日动态过滤 |
| 市值 | 总市值 > 20 亿元人民币 | 市值字段或总股本 * 收盘价 |
| 价格 | 最新收盘价 > 2 元 | `history_bars` 或 `get_price` |
| 流动性 | 过去 20 日平均成交额 > 2000 万元 | `total_turnover` 或 `close * volume` |
| 初始资金 | 1,000,000 元 | 股票账户初始资金 |
| 滑点 | 0.5% | 价格比例滑点 |
| 佣金 | 用米筐 A 股佣金设置，无法固定每笔时用费率近似 | 平台配置或代码配置 |
| 基准 | 中证 800 | 指数代码待账号内确认 |
| 回测区间 | Max 与最近 5 年 | 分别跑两次 |
| 主组合 | 30 只股票，等权，月度调仓 | `hold_count = 30` |

待米筐账号内确认的字段：中证 800 代码、总市值字段、成交额字段、ST 标识、停牌标识、上市日期、行业分类、财务因子字段名。

## 4. 股票池过滤

每个调仓日先生成候选股票池，再做排名。

过滤顺序：

1. 获取 A 股普通股票列表。
2. 剔除 ST、*ST。
3. 剔除停牌或不可交易股票。
4. 剔除上市未满 180 天的新股。
5. 剔除总市值不超过 20 亿元的股票。
6. 剔除最新收盘价不超过 2 元的股票。
7. 剔除过去 20 日平均成交额不超过 2000 万元的股票。
8. 剔除核心因子缺失过多的股票。

伪代码：

```python
def build_universe(context, bar_dict):
    stocks = get_all_a_shares(context.now)
    stocks = remove_st(stocks, context.now)
    stocks = remove_suspended(stocks, context.now, bar_dict)
    stocks = remove_new_stocks(stocks, context.now, min_days=180)
    stocks = filter_market_cap(stocks, context.now, min_cap=2_000_000_000)
    stocks = filter_price(stocks, context.now, min_price=2)
    stocks = filter_liquidity(stocks, context.now, min_avg_turnover=20_000_000)
    return stocks
```

## 5. 排名系统

策略名称：A 股 QVM-R 多因子纯多头策略。  
QVM-R = Quality + Value + Momentum + Risk penalty。

| 大类 | 权重 | 指标 | 方向 |
|---|---:|---|---|
| Quality 质量 | 35% | ROE、ROA、经营现金流/总资产、毛利率、资产负债率 | 前四个越高越好，资产负债率越低越好 |
| Value 价值 | 25% | EP、BP、现金流收益率、PE、PB | 前三个越高越好，PE/PB 越低越好 |
| Momentum 动量 | 25% | 过去 12 个月剔除最近 1 个月收益、过去 6 个月收益 | 越高越好 |
| Risk 风险惩罚 | 15% | 过去 6 个月波动率、过去 6 个月最大回撤 | 越低越好 |

标准化流程：

1. 对每个原始因子做 1%/99% 去极值。
2. 横截面 z-score 标准化。
3. 统一方向，负向指标乘以 -1。
4. 大类内部等权平均。
5. 大类之间按 35/25/25/15 合成。
6. 按综合得分从高到低排序。

综合得分：

```text
Score = 0.35 * Quality + 0.25 * Value + 0.25 * Momentum + 0.15 * RiskAdjusted
```

其中 `RiskAdjusted` 已经是“低波动、低回撤更高分”的方向。

缺失值处理：

- 单个因子缺失：优先用行业中位数填补；若行业字段不可用，用全市场中位数。
- 一只股票可用因子比例低于 70%：剔除。
- 财务字段明显异常：winsorize 后进入标准化，不做主观删除。

## 6. 交易规则

| 项目 | 标准版 |
|---|---|
| 持仓数量 | 30 只 |
| 权重 | 等权 |
| 调仓频率 | 每月第一个交易日 |
| 买入规则 | 买入综合排名前 30 |
| 卖出规则 | 跌出前 60，或不再满足股票池过滤，或停牌/不可交易 |
| 现金处理 | 尽量满仓，保留少量现金应付费用 |
| 单票上限 | 等权约 3.33% |
| 基准 | 中证 800 |
| 成本 | 0.5% 滑点 + 米筐佣金设置 |

用“跌出前 60 才卖出”的原因：

- 减少排名小幅波动造成的无效换手；
- 降低交易成本；
- 更适合月度中低频多因子策略。

## 7. 米筐策略代码结构

建议把策略写成参数化结构，方便敏感性测试。

```python
def initialize(context):
    context.hold_count = 30
    context.sell_rank = 60
    context.min_listed_days = 180
    context.min_market_cap = 2_000_000_000
    context.min_price = 2
    context.min_avg_turnover = 20_000_000
    context.use_momentum = True
    context.use_risk_penalty = True
    context.use_industry_cap = False
    context.industry_cap = 0.25
    scheduler.run_monthly(rebalance, tradingday=1)

def rebalance(context, bar_dict):
    universe = build_universe(context, bar_dict)
    factors = compute_factor_table(universe, context.now)
    scores = build_qvmr_score(factors, context)
    scores = apply_optional_constraints(scores, context)
    target = scores.sort_values("score", ascending=False).head(context.hold_count)

    current = list(context.portfolio.positions.keys())
    rank_map = scores["rank"].to_dict()

    for order_book_id in current:
        rank = rank_map.get(order_book_id)
        if rank is None or rank > context.sell_rank or order_book_id not in universe:
            order_target_percent(order_book_id, 0)

    weight = 0.98 / len(target)
    for order_book_id in target.index:
        order_target_percent(order_book_id, weight)
```

实际代码要根据米筐账号内字段名调整，不要在字段未验证前把字段名写死为最终版。

## 8. 米筐平台执行步骤

### 8.1 字段验证

在米筐投资研究 Notebook 中先做字段验证：

1. 拉取 A 股股票列表。
2. 抽样 5-10 只股票。
3. 查行情字段：close、volume、total_turnover。
4. 查状态字段：ST、停牌、上市日期。
5. 查财务字段：ROE、ROA、PE、PB、经营现金流、总资产、总市值。
6. 查行业字段。
7. 查中证 800 指数代码和行情。

输出：字段验证截图、可用字段表、替代字段表。

### 8.2 标准版回测

在米筐策略/回测页面执行：

1. 新建策略。
2. 粘贴标准版 QVM-R 代码。
3. 设置初始资金 1,000,000。
4. 设置基准为中证 800。
5. 设置日频回测。
6. 设置滑点 0.5%。
7. 设置佣金/交易成本。
8. 跑 Max 回测并保存结果。
9. 跑最近 5 年回测并保存结果。

### 8.3 敏感性测试

至少跑以下组合：

| 编号 | 测试 | 参数 |
|---|---|---|
| T0 | 标准版 | 30 只，月度，QVM-R，等权 |
| T1 | 持仓数 | 25 / 50 / 100 只 |
| T2 | 调仓频率 | 双周 / 月度 / 季度 |
| T3 | 无动量 | 去掉 Momentum，权重重分配到 Quality 和 Value |
| T4 | 无风险惩罚 | 去掉 Risk penalty |
| T5 | 行业约束 | 单行业权重不超过 25% |
| T6 | 波动率权重 | 按 1/vol 调整权重 |

每组记录：年化收益、累计收益、Sharpe、最大回撤、换手率、Alpha、Beta、相对基准收益。

## 9. 截图清单

必须截图：

- 排名系统分支或因子代码；
- 因子函数/字段验证结果；
- 回测参数设置；
- Max 回测总结页；
- 最近 5 年回测总结页；
- 收益曲线；
- 回撤曲线；
- 持仓分配图；
- 交易表现统计；
- 敏感性测试结果表或结果页。

截图命名建议：

```text
01_factor_tree.png
02_field_validation.png
03_backtest_settings_max.png
04_summary_max.png
05_summary_5y.png
06_holdings_allocation.png
07_trade_stats.png
08_sensitivity_table.png
```

## 10. 本地结果整理模板

标准版结果表：

| 区间 | 年化收益 | 累计收益 | Sharpe | 最大回撤 | 换手率 | Alpha | Beta | 备注 |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Max | 待填 | 待填 | 待填 | 待填 | 待填 | 待填 | 待填 | 米筐结果 |
| 最近 5 年 | 待填 | 待填 | 待填 | 待填 | 待填 | 待填 | 待填 | 米筐结果 |

敏感性测试表：

| 测试 | 参数 | 年化收益 | Sharpe | 最大回撤 | 换手率 | 结论 |
|---|---|---:|---:|---:|---:|---|
| T0 | 30 只，月度 | 待填 | 待填 | 待填 | 待填 | 基准策略 |
| T1 | 25/50/100 只 | 待填 | 待填 | 待填 | 待填 | 分散化影响 |
| T2 | 双周/月度/季度 | 待填 | 待填 | 待填 | 待填 | 调仓频率影响 |
| T3 | 无动量 | 待填 | 待填 | 待填 | 待填 | 动量贡献 |
| T4 | 无风险惩罚 | 待填 | 待填 | 待填 | 待填 | 风险控制贡献 |
| T5 | 行业约束 | 待填 | 待填 | 待填 | 待填 | 行业暴露控制 |
| T6 | 波动率权重 | 待填 | 待填 | 待填 | 待填 | 权重优化效果 |

## 11. 报告结构

建议报告按这个顺序写：

1. 摘要：策略目标、核心因子、主要结果。
2. 设计原则：多因子、质量价值动量、风险惩罚、低换手。
3. 排名系统：股票池、因子树、标准化、权重、缺失值处理。
4. 交易系统：持仓数、等权、月度调仓、买卖规则、成本、基准。
5. 回测结果：Max 与最近 5 年。
6. 敏感性测试：持仓数、调仓频率、因子开关、约束版本。
7. 创新点：风险惩罚、卖出缓冲区、行业约束/波动率权重。
8. 局限性：过拟合风险、因子拥挤、交易成本、市场风格切换。

## 12. 复核清单

跑正式回测前检查：

- 股票池过滤是否在排名前完成；
- 是否剔除 ST、停牌、新股；
- 是否使用成交额而不是错误的成交量口径；
- 是否避免未来函数；
- 财务数据是否使用可得时点数据；
- 回测成本是否包含滑点和佣金；
- Max 与最近 5 年是否分别运行；
- 敏感性测试是否只改一个主要参数；
- 截图是否能对应报告文字；
- 报告结论是否由回测结果支持。

# Deep Research 审查日志

项目：米筐 A 股量化交易系统期末作业  
日期：2026-06-12 至 2026-06-13  
用途：记录本次调研的证据来源、复核过程、风险项和补漏事项。

## 0. 当前主线更新

用户已明确当前项目采用米筐平台、A 股标的、全 A 股股票池、纯多头组合、中证 800 基准。旧的“米筐美股是否支持”核查只作为背景材料，不再作为后续执行主线。

当前主文档：

- `output/ricequant_a_share_execution_plan.md`
- `output/ricequant_implementation_spec.md`

最终报告不主动讨论市场从美股改为 A 股的合规问题，只呈现 A 股交易系统设计、执行和结果。

## 1. 调研轮次

### Round 1：本地材料确认

已检查文件：

- `期末小组项目.pdf`
- `量化多因子系列（1）：QQC综合质量因子与指数增强应用.pdf`
- `量化多因子系列（2）：非线性假设下的情景分析因子模型.pdf`
- `量化多因子系列（3）：如何捕捉成长与价值的风格轮动？(1).pdf`
- `量化多因子系列（4）：风格轮动模型与主动&被动量化产品的结合.pdf`
- `量化多因子系列（5）：基本面因子手册.pdf`
- `量化多因子系列（6）：关于动量，你所希望了解的那些事.pdf`
- `量化多因子系列（7）：价量因子手册.pdf`
- `量化多因子系列（8）：供应链如何实现动量传导？.pdf`
- `量化多因子系列（9）：宽基指数增强2.0体系.pdf`

复核结论：

- 作业 PDF 可抽取，硬性参数明确。
- 第 5、6、7 篇研报对主策略最有用。
- 第 4 篇 PDF 文本抽取质量较差，不作为核心证据。
- 研报多为 A 股研究，不能直接作为美股有效性的唯一依据。

### Round 2：米筐官方文档核查

已核查链接：

- https://www.ricequant.com/doc/quant/
- https://www.ricequant.com/doc/quant/research
- https://www.ricequant.com/doc/quant/factor-system
- https://www.ricequant.com/doc/quant/backtest
- https://www.ricequant.com/doc/quant/strategy-api
- https://www.ricequant.com/doc/rqalpha-plus/api/config
- https://www.ricequant.com/doc/rqdata/python/stock-mod
- https://www.ricequant.com/doc/rqfactor/manual/index-rqfactor
- https://www.ricequant.com/doc/rqpattr/doc/index-rqpattr

复核结论：

- 能确认回测、模拟交易、策略 API、滑点、佣金倍率、账户初始资金、基准、报告输出、因子研究和绩效归因能力。
- 能确认 `scheduler`、`history_bars`、`get_price`、`get_factor`、`all_instruments`、`order_target_percent` 等策略开发接口。
- 能确认网页平台层面的投资研究、因子研究和回测设置入口，包括起始资金、基准、滑点、撮合、成交量限制、买空设置、风险指标、持仓和交易数据获取。
- 不能从公开文档确认完整美股链路。

### Round 3：外部因子研究核查

已使用或核查的核心文献：

- Fama & French (1993)：价值/规模等共同风险因子。
- Fama & French (2015)：五因子模型，加入盈利能力和投资。
- Jegadeesh & Titman (1993)：中期动量。
- Carhart (1997)：四因子绩效归因，加入动量。
- Asness, Frazzini & Pedersen：Quality Minus Junk。
- Baker, Bradley & Wurgler：低波动异常相关研究。

复核结论：

- 价值、质量/盈利、动量、低波动均有外部研究支撑。
- 外部研究支持“因子类别”，不保证本策略参数在未来有效。
- 因子权重应固定为事前设计，避免看回测调参。

### Round 4：A 股主线重规划复核

已完成：

- 根据用户决策锁定米筐、A 股全市场、纯多头、中证 800、本地 Agent + 米筐协作。
- 新增 `ricequant_a_share_execution_plan.md` 作为当前执行计划。
- 重写 `ricequant_implementation_spec.md`，从“美股预检规格书”改为“A 股具体实施规格书”。
- 更新 `README.md`，把输出目录入口改为 A 股主线。
- 保留早期美股支持核查文件，但明确其为归档背景材料。

复核结论：

- 当前项目的关键问题已经从“米筐是否支持美股”切换为“A 股字段、基准、佣金、截图和代码执行是否逐项落实”。
- 本地 Agent 的职责是策略设计、代码草稿、执行手册、结果整理、报告写作；米筐的职责是数据验证、策略运行、回测结果、图表和截图。
- 后续不得再把 P123 或美股作为主方案，除非用户重新要求。

## 2. 证据质量矩阵

| 来源 | 类型 | 质量等级 | 用途 | 限制 |
|---|---|---|---|---|
| 作业 PDF | 课程原始要求 | 高 | 定义硬性约束和交付物 | 只有 2 页，未解释平台细节 |
| 米筐官方文档 | 官方平台文档 | 高 | 确认 API、配置和平台能力 | 公开文档未确认美股 |
| 中金多因子研报 | 卖方研究 | 中高 | 因子工程、组合设计、A 股经验 | 市场为 A 股，存在迁移风险 |
| Fama-French | 学术研究 | 高 | 价值、盈利等因子理论基础 | 不是具体策略说明书 |
| Jegadeesh-Titman / Carhart | 学术研究 | 高 | 动量因子理论基础 | 动量表现有周期性 |
| Asness QMJ | 学术/工作论文 | 中高 | 质量因子体系 | 不同版本和市场定义可能不同 |
| 低波动研究 | 学术/实务研究 | 中高 | 风险惩罚和回撤控制 | 低波动不一定总提升收益 |

## 3. Devil's Advocate 审查

### 问题 1：A 股参数是等价口径，不是原题逐字口径

严重性：Major  
影响：如果报告展开解释市场替换，反而会把注意力引到合规争议。  
处理：最终报告只写 A 股交易系统参数，不主动讨论美股/A 股差异；内部执行文档保留参数映射。

### 问题 2：米筐字段名必须账号内复核

严重性：Major  
影响：如果总市值、成交额、ST、停牌、行业、财务字段名不一致，代码会运行失败。  
处理：把字段验证放在策略代码前，先输出字段验证截图和替代字段表。

### 问题 3：多因子模型容易变成堆指标

严重性：Major  
影响：因子太多会降低解释力并增加过拟合嫌疑。  
处理：主策略只保留四个大类；细分因子在大类内等权，权重事前固定。

### 问题 4：佣金设置可能无法精确等价为原题每笔固定佣金

严重性：Major  
影响：交易成本不匹配会影响回测可比性。  
处理：A 股主线使用米筐可配置佣金或费率近似；报告写清交易成本假设，不把成本调参作为收益来源。

### 问题 5：创新测试可能增加过拟合嫌疑

严重性：Minor 到 Major  
影响：如果展示太多结果，老师可能认为是结果导向调参。  
处理：主策略参数事前固定；创新测试用于解释稳健性和机制，不用“表现最好的一组”替代主策略。

## 4. 最终补漏清单

账号实测前仍需确认：

- A 股股票池 API 写法。
- 中证 800 基准代码。
- 总市值字段。
- 成交额字段或 `close * volume` 是否可接受。
- ST 标识字段。
- 停牌/可交易状态字段。
- 上市日期字段。
- 行业分类字段。
- ROE、ROA、PE、PB、经营现金流、总资产等财务字段。
- 米筐佣金和滑点设置方式。
- Max 最早可回测日期。
- 是否能导出持仓分配图和绩效统计截图。

报告写作前仍需补：

- 实际回测结果表。
- Max 和 5 年截图。
- 策略参数敏感性结果。
- 截图文件索引。
- 字段验证截图。

## 5. 文件输出

已生成：

- `output/ricequant_deep_research_report.md`
- `output/ricequant_implementation_spec.md`
- `output/research_audit_log.md`
- `output/ricequant_a_share_execution_plan.md`
- `output/ricequant_us_stock_support_verification.md`

编码检查：

- `ricequant_deep_research_report.md`：UTF-8 通过。
- `ricequant_implementation_spec.md`：UTF-8 通过。
- `ricequant_a_share_execution_plan.md`：UTF-8 通过。

## 6. 审查结论

本次调研已经从“米筐美股可行性”重新收束为“米筐 A 股可执行项目”。当前未决项不再是是否做美股，而是 A 股字段、基准代码、佣金/滑点设置和截图位置的账号内验证。后续行动应先做字段验证，再写策略代码和跑标准版回测。

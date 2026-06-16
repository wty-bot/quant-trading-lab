# 米筐 A 股策略字段可用性表

当前环境：`D:\Miniconda3\envs\ricequant-final`  
数据组件：`rqdatac==3.5.2`，`rqalpha-plus==4.4.3`

| 模块 | 作业/策略需求 | 米筐已验证字段或接口 | 状态 |
|---|---|---|---|
| 股票池 | 全 A 股列表 | `rqdatac.all_instruments(type="CS", market="cn")` | 可直接用 |
| 状态 | ST / *ST | `special_type`，`rqdatac.is_st_stock` | 可直接用 |
| 状态 | 停牌 | `rqdatac.is_suspended` | 可直接用 |
| 状态 | 上市日期 | `listed_date` | 可直接用 |
| 行情 | 收盘价 | `rqdatac.get_price(..., fields="close")` / RQAlpha `history_bars` | 可直接用 |
| 行情 | 成交额 | `total_turnover` | 可直接用 |
| 行情 | 成交量 | `volume` | 可直接用 |
| 基准 | 中证 800 | `000906.XSHG` | 可直接用 |
| 价值 | 总市值 | `market_cap` | 可直接用 |
| 价值 | PE | `pe_ratio_ttm` | 可直接用，负值需处理 |
| 价值 | PB | `pb_ratio_ttm` | 可直接用 |
| 价值 | BP | `book_to_market_ratio_ttm` | 可直接用 |
| 质量 | ROE | `return_on_equity_ttm` | 可直接用 |
| 质量 | ROA | `return_on_asset_ttm` | 可直接用 |
| 质量 | 毛利率 | `gross_profit_margin_ttm` | 可直接用 |
| 质量 | 经营现金流质量 | `ocf_to_debt_ttm` 等现金流类字段 | 可替代，需要后续筛选 |
| 动量 | 6 月/12-1 月收益 | 用历史价格自行计算 | 可实现 |
| 风险 | 波动率/回撤 | 用历史价格自行计算 | 可实现 |

最小回测已通过：

- 策略文件：`rq_minimal_buy_hold.py`
- 数据包：`D:\RiceQuantData\bundle_sample\bundle`
- 报告目录：`D:\RiceQuantResults\minimal_report`
- 基准：`000906.XSHG`

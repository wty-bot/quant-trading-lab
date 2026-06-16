# 米筐是否支持美股：专项复核结论

复核日期：2026-06-13  
检索工具：AnySearch  
结论等级：高置信度

## 结论

按公开官方文档，米筐/RQData/RQAlpha Plus **不支持本作业所需的标准美股完整链路**。

这里的“标准美股完整链路”指：

- 美股股票池；
- 美股日行情；
- 美股市值、成交额、收盘价过滤；
- 美股财务因子；
- 美股回测；
- S&P 500 或 SPY 基准/对冲；
- 美元账户和每笔 8 美元佣金。

公开文档没有给出上述链路。相反，官方文档显示的可用市场主要是中国内地和香港。

## 核心证据

### 1. RQData 官方首页列出的数据范围没有美股

RQData Python API 手册写明每日更新数据包括：

- 中国 A 股；
- 场内基金，如 ETF、LOF；
- 可转债；
- 中国期货；
- 中国期权；
- 国债逆回购；
- 现货，上金所；
- 舆情大数据；
- 因子协方差、特异风险和收益率。

来源：https://www.ricequant.com/doc/rqdata/python/index-rqdatac

### 2. RQData 文档目录没有美股模块

RQData API 目录列出的模块包括：

- A 股；
- 港股；
- 金融、商品期货；
- 金融、商品期权；
- 指数、场内基金；
- 基金；
- 可转债；
- 风险因子；
- 现货；
- 货币市场；
- 宏观经济数据；
- 另类数据；
- 米筐特色指数。

没有 US stock / 美股模块。

来源：https://www.ricequant.com/doc/rqdata/python/index-rqdatac

### 3. 通用 API 的 market 参数只列 cn/hk

`all_instruments(type=None, date=None, market='cn')` 文档说明：

- `market='cn'`：中国内地市场；
- `market='hk'`：香港市场。

`instruments(order_book_ids, market='cn')` 也是同样的市场参数，并且证券代码说明只列：

- `.XSHG`：上证；
- `.XSHE`：深证；
- `.XHKG`：港股。

来源：https://www.ricequant.com/doc/rqdata/python/generic-api

### 4. get_price 说明是中国市场合约，不是美股

`get_price(..., market='cn')` 文档写的是支持股票、期货、期权、可转债、ETF、常见指数等中国市场合约，也包括上金所现货中的黄金、铂金、白银产品。

来源：https://www.ricequant.com/doc/rqdata/python/generic-api

### 5. 股票财务数据是 A 股财务数据

股票数据页标题为“A 股财务数据”，并且 `get_pit_financials_ex` 的 market 参数说明支持：

- `cn`：中国内地市场；
- `hk`：香港市场。

没有美股财务字段。

来源：https://www.ricequant.com/doc/rqdata/python/stock-mod

### 6. 反向检索没有找到美股官方支持证据

AnySearch 检索：

- `market='us' rqdatac`
- `market="us" rqdatac`
- `XNAS ricequant`
- `NYSE rqdatac`
- `美股 rqdatac`

没有找到米筐官方 API 支持美股的证据。

### 7. 第三方旁证

一篇 rqalpha 入门文章明确写到：`rqalpha不支持港美股回测&交易，可以自定义支持，但成本不小`。

来源：https://rchardzhu.github.io/2022/03/26/start-to-learn-rqalpha/

这不是官方证据，只能作为旁证；但它与官方文档的市场范围一致。

## 判断

原先报告里写“未能确认美股支持”太保守。更准确的写法应该是：

> 公开官方文档不支持米筐完成本作业的美股标准参数；除非你的账号存在未公开的机构定制权限，否则不应把米筐美股作为主方案。

## 对作业的影响

你的作业原文要求：

- 美股；
- S&P 500 对冲可选；
- `Mktcap > 200`；
- `close(0) > 2`；
- `Avgdailytot(20) > 200000`；
- 100 万美元；
- 每笔 8 美元佣金。

这些字段和参数风格更接近 P123 的美股策略平台，而不是米筐公开文档里的市场结构。

## 建议

### 最稳妥

如果老师坚持美股，用 P123。

### 如果必须用米筐

向老师说明米筐公开文档不支持美股完整链路，申请改为：

- A 股版本：基准用沪深 300 或中证 500；
- 或港股版本：基准用恒生指数/合适港股指数。

策略框架仍可保留 QVM-R：Quality + Value + Momentum + Risk penalty。

### 如果还想最后确认账号隐藏权限

登录米筐后只需快速测试：

```python
all_instruments(type='CS', market='us')
instruments('AAPL', market='us')
get_price('AAPL', start_date='2020-01-01', end_date='2020-01-10', market='us')
get_factor(['AAPL'], ['pe_ratio', 'market_cap'], '2020-01-10')
```

如果任一核心接口失败，就不要继续用米筐做美股。

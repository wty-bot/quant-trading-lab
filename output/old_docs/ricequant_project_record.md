# 米筐 RQSDK 项目当前记录

记录时间：2026-06-15

## 1. 当前目标

本项目使用米筐 RQSDK / RQData / RQAlpha Plus 完成 A 股基本面量化交易期末作业。

当前阶段不是策略优化，而是先把正式回测所需的本地 `bundle` 数据包下载完整。只有数据包完整后，才进入正式策略回测。

## 2. 已安装环境

- Miniconda 安装位置：`D:\Miniconda3`
- Conda 环境：`ricequant-final`
- Python：`3.11.15`
- RQSDK：`1.7.2`
- RQData：`3.5.2`
- RQAlpha Plus：`4.4.3`

常用可执行文件：

```powershell
D:\Miniconda3\envs\ricequant-final\python.exe
D:\Miniconda3\envs\ricequant-final\Scripts\rqsdk.exe
D:\Miniconda3\envs\ricequant-final\Scripts\rqalpha-plus.exe
```

## 3. License 配置方式

不要把 License Key 写入项目文件、策略文件、报告或 Git。

官方配置方式：

```powershell
rqsdk license -l <license_key>
```

该命令会将裸 key 转为类似下面的 RQData URI：

```text
tcp://license:<license_key>@rqdatad-pro.ricequant.com:16011
```

然后写入用户级环境变量：

```text
RQSDK_LICENSE
RQDATAC_CONF
```

在新的 PowerShell 子进程中运行米筐命令前，建议先注入用户级环境变量：

```powershell
$env:RQDATAC_CONF = [Environment]::GetEnvironmentVariable('RQDATAC_CONF','User')
$env:RQSDK_LICENSE = [Environment]::GetEnvironmentVariable('RQSDK_LICENSE','User')
```

注意：刚才有一次新 key 失败，是因为复制时漏掉末尾的 `=`。补全后同一个 key 已成功校验并用于继续下载。

## 4. 数据包路径与重要发现

米筐 `rqsdk update-data -d <path>` 的实现会在 `<path>` 下再拼一层 `bundle`。

因此：

```powershell
rqsdk update-data --base -d D:\RiceQuantData\bundle_sample\bundle -c 1
```

实际写入目录是：

```text
D:\RiceQuantData\bundle_sample\bundle\bundle
```

当前半成品正式数据包就在这个嵌套目录里：

```text
D:\RiceQuantData\bundle_sample\bundle\bundle
```

虽然路径不美观，但当前为了节省流量，不应重建目录或重头下载。后续应继续沿用该目录接力下载。

## 5. 当前下载进度

最初样例包路径：

```text
D:\RiceQuantData\bundle_sample\bundle
```

样例包仍在，未被破坏。

当前继续下载形成的半成品路径：

```text
D:\RiceQuantData\bundle_sample\bundle\bundle
```

当前文件状态：

```text
stocks.h5          1,012,863,248 bytes
indexes.h5         800 bytes
funds.h5           800 bytes
futures.h5         800 bytes
trading_dates.npy  22,476 bytes
```

`stocks.h5` 当前状态：

- 已包含股票数：`3802`
- 第一只：`000001.XSHE`
- 当前最后写到：`600834.XSHG`
- 新版字段有效，包含：
  - `datetime`
  - `open`
  - `close`
  - `high`
  - `low`
  - `prev_close`
  - `limit_up`
  - `limit_down`
  - `volume`
  - `total_turnover`

这说明数据可以接着下，不需要从头重下已写入的股票。

## 6. 已用过的额度情况

第一个教育版 key：

- 初始流量：`200MB`
- 在错误路径尝试和第一次正式下载中被耗尽
- 最后显示剩余约：`-7.48MB`
- 当时 `stocks.h5` 写到约 `1475` 只股票，最后为 `002884.XSHE`

第二个教育版 key：

- 初始流量：`200MB`
- 校验成功后继续接力下载
- 最后显示已用：`202.57MB`
- 剩余：`-2.57MB`
- `stocks.h5` 从 `1475` 只推进到 `3802` 只，最后为 `600834.XSHG`

## 7. 后续接力下载命令

换下一个新额度 key 后，先配置：

```powershell
rqsdk license -l <license_key>
```

再注入环境变量：

```powershell
$env:RQDATAC_CONF = [Environment]::GetEnvironmentVariable('RQDATAC_CONF','User')
$env:RQSDK_LICENSE = [Environment]::GetEnvironmentVariable('RQSDK_LICENSE','User')
```

继续接力下载：

```powershell
D:\Miniconda3\envs\ricequant-final\Scripts\rqsdk.exe update-data --base -d D:\RiceQuantData\bundle_sample\bundle -c 1
```

不要改成：

```powershell
-d D:\RiceQuantData\bundle_sample\bundle\bundle
```

否则会再嵌套出第三层 `bundle`。

## 8. 现在不要做的事

在数据包完整前，不要做以下事情：

- 不要拿样例包跑正式策略回测。
- 不要跑正式 QVMR 多因子策略回测。
- 不要下载分钟线：不要加 `--minbar`。
- 不要下载 tick：不要加 `--tick`。
- 不要清理或移动 `D:\RiceQuantData\bundle_sample\bundle\bundle`。
- 不要把任何 License Key 写入 Markdown、Python、报告或 Git。

## 9. 判断数据完整的标准

当前只完成了部分 `stocks.h5`。

正式回测前至少需要：

- `stocks.h5` 全 A 股日线补全。
- `indexes.h5` 不再是 800 bytes，并包含正式指数日线。
- `trading_dates.npy` 存在且可读。
- ST、停牌、分红、复权等基础文件完整生成。
- `rqsdk update-data --base` 能完整退出，且不再因 quota 中断。

数据完整后，再进行：

```powershell
rqalpha-plus run ...
```

正式回测时 `-d` 应指向真实 bundle 目录：

```powershell
-d D:\RiceQuantData\bundle_sample\bundle\bundle
```

## 10. 下一步

继续提供新的有效教育版 License Key。

每个 key 的处理顺序：

1. 先用 RQData 直连校验额度。
2. 用 `rqsdk license -l <license_key>` 写入官方环境变量。
3. 执行 `update-data --base -d D:\RiceQuantData\bundle_sample\bundle -c 1`。
4. 等命令自然结束或 quota 耗尽。
5. 检查 `stocks.h5` 写到哪只股票。
6. 继续下一个 key。

## 11. 2026-06-16 追加下载记录

2026-06-16 继续使用刷新后的教育版额度和一个新教育版 key 接力下载，仍然只执行官方：

```powershell
rqsdk update-data --base -d D:\RiceQuantData\bundle_sample\bundle -c 1
```

没有下载分钟线或 tick。

### 2026-06-16 下载前状态

```text
stocks.h5   1,278,396,432 bytes，5509 只股票
indexes.h5    738,382,304 bytes，3328 个指数，含 000906.XSHG
```

仍缺：

```text
instruments.pk
st_stock_days.h5
suspended_days.h5
dividends.h5
split_factor.h5
ex_cum_factor.h5
yield_curve.h5
future_info.json
share_transformation.json
```

### 2026-06-16 下载后状态

最新半成品目录仍为：

```text
D:\RiceQuantData\bundle_sample\bundle\bundle
```

当前文件状态：

```text
stocks.h5          1,395,888,912 bytes，5509 只股票
indexes.h5         1,395,416,528 bytes，6449 个指数，含 000906.XSHG
futures.h5         800 bytes，空壳
funds.h5           800 bytes，空壳
trading_dates.npy  22,476 bytes
```

仍缺：

```text
instruments.pk
st_stock_days.h5
suspended_days.h5
dividends.h5
split_factor.h5
ex_cum_factor.h5
yield_curve.h5
future_info.json
share_transformation.json
```

本轮新 key 已耗尽：

```text
bytes_used 约 202.66 MB
bytes_left 约 -2.66 MB
```

### 当前判断

股票和指数日线主体已经较完整，且作业所需基准 `000906.XSHG` 已在指数数据中。

但官方 `--base` 流程仍未跑到基础文件生成阶段，所以正式回测所需的股票身份、ST、停牌、分红、拆股/复权等文件仍未补齐。

如果马上开始回测，只适合做代码调试或受限股票池的试跑，不适合作为最终提交结果。

from __future__ import annotations

import json
import pickle
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Iterable

import h5py
import numpy as np
import pandas as pd


DATASET_DIR = Path(r"D:\RiceQuantData\backtest_dataset")
EXPECTED_FACTORS = [
    "market_cap",
    "pe_ratio_ttm",
    "pb_ratio_ttm",
    "book_to_market_ratio_ttm",
    "return_on_equity_ttm",
    "return_on_asset_ttm",
    "gross_profit_margin_ttm",
    "ocf_to_debt_ttm",
]
INDUSTRY_COLUMNS = [
    "order_book_id",
    "sector_code",
    "sector_code_name",
    "industry_code",
    "industry_name",
]
PRICE_FEATURE_CACHE_FILE = Path(__file__).resolve().parents[2] / "reports" / "cache" / "price_feature_monthly.pkl"


def _date_str(date) -> str:
    return pd.Timestamp(date).strftime("%Y-%m-%d")


def _item_path(manifest: dict, key: str) -> Path:
    for item in manifest.get("items", []):
        if item.get("key") == key:
            return Path(item.get("absolute_path") or DATASET_DIR / item["file"])
    raise KeyError(f"manifest item not found: {key}")


def _read_pickle(path: Path):
    with path.open("rb") as fh:
        return pickle.load(fh)


@lru_cache(maxsize=1)
def load_manifest() -> dict:
    path = DATASET_DIR / "manifest.json"
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _rebalance_dates_all() -> tuple[str, ...]:
    manifest = load_manifest()
    paths = [_item_path(manifest, "rebalance_dates_pre5y"), _item_path(manifest, "rebalance_dates_5y")]
    dates: list[str] = []
    for path in paths:
        df = pd.read_csv(path)
        col = "date" if "date" in df.columns else df.columns[0]
        dates.extend(pd.to_datetime(df[col]).dt.strftime("%Y-%m-%d").tolist())
    return tuple(sorted(set(dates)))


def get_rebalance_dates(start, end, frequency: str = "monthly") -> list[str]:
    start_ts, end_ts = pd.Timestamp(start), pd.Timestamp(end)
    dates = [d for d in _rebalance_dates_all() if start_ts <= pd.Timestamp(d) <= end_ts]
    if frequency == "monthly":
        return dates
    if frequency == "quarterly":
        return [d for d in dates if pd.Timestamp(d).month in (3, 6, 9, 12)]
    raise ValueError(f"unsupported frequency: {frequency}")


@lru_cache(maxsize=1)
def _instrument_history() -> pd.DataFrame:
    obj = _read_pickle(_item_path(load_manifest(), "instruments_monthly"))
    df = obj["data"].copy()
    source_date_col = "date" if "date" in df.columns else "snapshot_date"
    df["date"] = pd.to_datetime(df[source_date_col]).dt.strftime("%Y-%m-%d")
    df["listed_date"] = pd.to_datetime(df["listed_date"], errors="coerce")
    de_listed = df["de_listed_date"].replace({"0000-00-00": pd.NA})
    df["de_listed_date"] = pd.to_datetime(de_listed, errors="coerce")
    return df


@lru_cache(maxsize=1)
def _factor_history() -> pd.DataFrame:
    obj = _read_pickle(_item_path(load_manifest(), "factors_monthly"))
    df = obj["data"].copy()
    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
    return df


@lru_cache(maxsize=1)
def _status_history() -> dict:
    manifest = load_manifest()
    merged = {"dates": [], "is_st_stock": {}, "is_suspended": {}}
    for key in ("status_pre5y", "status_5y"):
        obj = _read_pickle(_item_path(manifest, key))
        merged["dates"].extend(obj["dates"])
        merged["is_st_stock"].update(obj["is_st_stock"])
        merged["is_suspended"].update(obj["is_suspended"])
    merged["dates"] = sorted(set(merged["dates"]))
    return merged


@lru_cache(maxsize=1)
def _trading_dates() -> pd.DatetimeIndex:
    arr = np.load(_item_path(load_manifest(), "trading_calendar"), allow_pickle=True)
    return pd.DatetimeIndex(pd.to_datetime(arr.astype(str))).sort_values()


def get_instrument_snapshot(date) -> pd.DataFrame:
    date = _date_str(date)
    df = _instrument_history()
    out = df.loc[df["date"] == date].copy()
    if out.empty:
        raise KeyError(f"instrument snapshot not found for {date}")
    return out


def get_status_snapshot(date) -> pd.DataFrame:
    date = _date_str(date)
    hist = _status_history()
    if date not in hist["is_st_stock"] or date not in hist["is_suspended"]:
        raise KeyError(f"status snapshot not found for {date}")
    st = hist["is_st_stock"][date].iloc[0].rename("is_st")
    suspended = hist["is_suspended"][date].iloc[0].rename("is_suspended")
    return pd.concat([st, suspended], axis=1).rename_axis("order_book_id").reset_index()


def get_factor_snapshot(date) -> pd.DataFrame:
    date = _date_str(date)
    df = _factor_history()
    out = df.loc[df["date"] == date].copy()
    if out.empty:
        raise KeyError(f"factor snapshot not found for {date}")
    return out.set_index("order_book_id")


def get_industry_snapshot(date) -> pd.DataFrame:
    df = get_instrument_snapshot(date)
    cols = [c for c in INDUSTRY_COLUMNS if c in df.columns]
    if "order_book_id" not in cols:
        return pd.DataFrame(columns=INDUSTRY_COLUMNS)
    return df[cols].copy()


@lru_cache(maxsize=8192)
def _price_dataset_to_frame(order_book_id: str) -> pd.DataFrame:
    path = _item_path(load_manifest(), "prices")
    with h5py.File(path, "r") as h5:
        if order_book_id not in h5:
            return pd.DataFrame()
        arr = h5[order_book_id][:]
    df = pd.DataFrame.from_records(arr)
    df["date"] = pd.to_datetime(df["datetime"].astype(str).str[:8], format="%Y%m%d")
    df["order_book_id"] = order_book_id
    return df.drop(columns=["datetime"])


def _price_records_to_frame(order_book_id: str, arr, start_ts: pd.Timestamp, end_ts: pd.Timestamp) -> pd.DataFrame:
    date_int = arr["datetime"] // 1_000_000
    start_int = int(start_ts.strftime("%Y%m%d"))
    end_int = int(end_ts.strftime("%Y%m%d"))
    sub = arr[(date_int >= start_int) & (date_int <= end_int)]
    if len(sub) == 0:
        return pd.DataFrame()
    df = pd.DataFrame.from_records(sub)
    df["date"] = pd.to_datetime(df["datetime"].astype(str).str[:8], format="%Y%m%d")
    df["order_book_id"] = order_book_id
    return df.drop(columns=["datetime"])


def get_price_window(order_book_ids: Iterable[str], end_date, lookback: int) -> pd.DataFrame:
    end_ts = pd.Timestamp(end_date)
    calendar = _trading_dates()
    eligible = calendar[calendar <= end_ts]
    if eligible.empty:
        return pd.DataFrame()
    start_ts = eligible[max(0, len(eligible) - lookback)].normalize()
    frames = []
    for order_book_id in list(order_book_ids):
        df = _price_dataset_to_frame(order_book_id)
        if df.empty:
            continue
        mask = (df["date"] >= start_ts) & (df["date"] <= end_ts)
        if mask.any():
            frames.append(df.loc[mask])
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def get_index_price(order_book_id: str = "000906.XSHG", start=None, end=None) -> pd.DataFrame:
    path = _item_path(load_manifest(), "benchmark")
    with h5py.File(path, "r") as h5:
        if order_book_id not in h5:
            raise KeyError(order_book_id)
        arr = h5[order_book_id][:]
    df = pd.DataFrame.from_records(arr)
    df["date"] = pd.to_datetime(df["datetime"].astype(str).str[:8], format="%Y%m%d")
    df = df.drop(columns=["datetime"])
    if start is not None:
        df = df.loc[df["date"] >= pd.Timestamp(start)]
    if end is not None:
        df = df.loc[df["date"] <= pd.Timestamp(end)]
    return df.reset_index(drop=True)


def get_yield_curve(start=None, end=None) -> pd.DataFrame:
    manifest = load_manifest()
    frames = []
    for key in ("yield_curve_pre5y", "yield_curve_5y"):
        try:
            obj = _read_pickle(_item_path(manifest, key))
        except KeyError:
            continue
        if isinstance(obj, pd.DataFrame):
            frames.append(obj.copy())
        elif isinstance(obj, dict):
            for value in obj.values():
                if isinstance(value, pd.DataFrame):
                    frames.append(value.copy())
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames, ignore_index=False)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
    else:
        df = df.reset_index().rename(columns={df.reset_index().columns[0]: "date"})
        df["date"] = pd.to_datetime(df["date"])
    df = df.drop_duplicates(subset=["date"]).sort_values("date")
    if start is not None:
        df = df.loc[df["date"] >= pd.Timestamp(start)]
    if end is not None:
        df = df.loc[df["date"] <= pd.Timestamp(end)]
    return df.reset_index(drop=True)


def price_feature_cache_path() -> Path:
    return PRICE_FEATURE_CACHE_FILE


def build_price_feature_cache(force: bool = False) -> dict:
    path = price_feature_cache_path()
    if path.exists() and not force:
        return _read_pickle(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rebalance_dates = list(_rebalance_dates_all())
    rebalance_idx = pd.DatetimeIndex(pd.to_datetime(rebalance_dates))
    manifest = load_manifest()
    frames = []
    with h5py.File(_item_path(manifest, "prices"), "r") as h5:
        for order_book_id in h5.keys():
            arr = h5[order_book_id][:]
            dates = pd.to_datetime((arr["datetime"] // 1_000_000).astype(str), format="%Y%m%d")
            close = pd.Series(arr["close"], index=dates)
            turnover = pd.Series(arr["total_turnover"], index=dates)
            feat = pd.DataFrame(index=rebalance_idx)
            feat["close"] = close.reindex(rebalance_idx)
            feat["avg_turnover_20"] = turnover.rolling(20).mean().reindex(rebalance_idx)
            feat["avg_turnover_60"] = turnover.rolling(60).mean().reindex(rebalance_idx)
            feat["momentum_12_1"] = close.shift(21).div(close.shift(252)).sub(1).reindex(rebalance_idx)
            feat["momentum_63"] = close.div(close.shift(63)).sub(1).reindex(rebalance_idx)
            feat["momentum_126"] = close.div(close.shift(126)).sub(1).reindex(rebalance_idx)
            feat["momentum_252"] = close.div(close.shift(252)).sub(1).reindex(rebalance_idx)
            feat["ma_20_ratio"] = close.div(close.rolling(20).mean()).sub(1).reindex(rebalance_idx)
            feat["ma_60_ratio"] = close.div(close.rolling(60).mean()).sub(1).reindex(rebalance_idx)
            feat["ma_120_ratio"] = close.div(close.rolling(120).mean()).sub(1).reindex(rebalance_idx)
            feat["high_252_ratio"] = close.div(close.rolling(252).max()).sub(1).reindex(rebalance_idx)
            feat["vol_120"] = close.pct_change().rolling(120).std().reindex(rebalance_idx)
            returns = close.pct_change()
            feat["downside_vol_120"] = returns.where(returns < 0).rolling(120, min_periods=60).std().reindex(rebalance_idx)
            rolling_peak = close.rolling(252, min_periods=120).max()
            feat["drawdown_252"] = close.div(rolling_peak).sub(1).reindex(rebalance_idx)
            feat["turnover_trend_20_60"] = feat["avg_turnover_20"].div(feat["avg_turnover_60"]).sub(1)
            feat["order_book_id"] = order_book_id
            feat["date"] = feat.index.strftime("%Y-%m-%d")
            frames.append(feat.reset_index(drop=True))
    all_feat = pd.concat(frames, ignore_index=True)
    data = {
        date: frame.drop(columns=["date"]).set_index("order_book_id")
        for date, frame in all_feat.groupby("date", sort=True)
    }
    cache = {"dates": rebalance_dates, "data": data}
    with path.open("wb") as fh:
        pickle.dump(cache, fh, protocol=pickle.HIGHEST_PROTOCOL)
    return cache


@lru_cache(maxsize=1)
def load_price_feature_cache() -> dict:
    path = price_feature_cache_path()
    if not path.exists():
        return build_price_feature_cache(force=False)
    return _read_pickle(path)


def get_price_feature_snapshot(date) -> pd.DataFrame:
    cache = load_price_feature_cache()
    key = _date_str(date)
    if key not in cache["data"]:
        raise KeyError(f"price feature snapshot not found for {key}")
    return cache["data"][key].copy()


@dataclass(frozen=True)
class DatasetCheck:
    manifest_items: int
    stock_keys: list[str]
    factor_shape: tuple[int, int]
    expected_factors_present: dict[str, bool]
    industry_columns_present: dict[str, bool]
    price_feature_cache_exists: bool = False


def validate_dataset() -> DatasetCheck:
    manifest = load_manifest()
    with h5py.File(_item_path(manifest, "prices"), "r") as h5:
        stock_keys = list(h5.keys())[:5]
    factors = _factor_history()
    instruments = _instrument_history()
    return DatasetCheck(
        manifest_items=len(manifest.get("items", [])),
        stock_keys=stock_keys,
        factor_shape=tuple(factors.shape),
        expected_factors_present={col: col in factors.columns for col in EXPECTED_FACTORS},
        industry_columns_present={col: col in instruments.columns for col in INDUSTRY_COLUMNS if col != "order_book_id"},
        price_feature_cache_exists=price_feature_cache_path().exists(),
    )

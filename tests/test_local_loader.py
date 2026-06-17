import pandas as pd

from src.data.local_loader import (
    EXPECTED_FACTORS,
    get_factor_snapshot,
    get_industry_snapshot,
    get_instrument_snapshot,
    get_price_window,
    get_rebalance_dates,
    get_status_snapshot,
    load_manifest,
    validate_dataset,
)


def test_manifest_and_dataset_check():
    manifest = load_manifest()
    check = validate_dataset()
    assert manifest["dataset_name"] == "ricequant_a_share_backtest_dataset"
    assert check.manifest_items >= 8
    assert len(check.stock_keys) == 5
    assert all(check.expected_factors_present.values())
    assert check.industry_columns_present["industry_name"]


def test_core_snapshots_return_expected_types():
    date = get_rebalance_dates("2021-06-30", "2021-06-30")[0]
    instruments = get_instrument_snapshot(date)
    status = get_status_snapshot(date)
    factors = get_factor_snapshot(date)
    industry = get_industry_snapshot(date)
    prices = get_price_window(["000001.XSHE", "000002.XSHE"], date, 25)

    assert not instruments.empty
    assert {"order_book_id", "status", "type", "listed_date"}.issubset(instruments.columns)
    assert {"order_book_id", "is_st", "is_suspended"}.issubset(status.columns)
    assert all(col in factors.columns for col in EXPECTED_FACTORS)
    assert {"order_book_id", "sector_code", "industry_name"}.issubset(industry.columns)
    assert not prices.empty
    assert pd.api.types.is_datetime64_any_dtype(prices["date"])


def test_rebalance_dates_and_quarterly_filter():
    monthly = get_rebalance_dates("2021-06-30", "2021-12-31")
    quarterly = get_rebalance_dates("2021-06-30", "2021-12-31", frequency="quarterly")
    assert monthly[0] == "2021-06-30"
    assert set(quarterly).issubset(monthly)
    assert all(pd.Timestamp(d).month in (3, 6, 9, 12) for d in quarterly)

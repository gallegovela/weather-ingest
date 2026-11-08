"""Unit tests for ingest/metrics.py's pure calculations.

See spec/testing.md and spec/ingest/METRICS.md: the day-over-day
temperature differences (including the "no previous day row" case)
and the rainy-day classification, no network/database involved.
"""

from datetime import date
from decimal import Decimal

from ingest.metrics import compute_day_metrics, is_rainy_day

STATION_CODE = "3195"
TARGET_DATE = date(2024, 1, 2)


def test_temperature_range_computed_when_both_values_present():
    today = {"max_temperature": Decimal("20.0"), "min_temperature": Decimal("8.0")}
    result = compute_day_metrics(STATION_CODE, TARGET_DATE, today, None)
    assert result["temperature_range"] == Decimal("12.0")


def test_temperature_range_null_when_max_missing():
    today = {"max_temperature": None, "min_temperature": Decimal("8.0")}
    result = compute_day_metrics(STATION_CODE, TARGET_DATE, today, None)
    assert result["temperature_range"] is None


def test_diff_prev_day_computed_when_both_days_present():
    today = {"max_temperature": Decimal("20.0"), "min_temperature": Decimal("8.0")}
    yesterday = {"max_temperature": Decimal("18.0"), "min_temperature": Decimal("5.0")}
    result = compute_day_metrics(STATION_CODE, TARGET_DATE, today, yesterday)
    assert result["max_temperature_diff_prev_day"] == Decimal("2.0")
    assert result["min_temperature_diff_prev_day"] == Decimal("3.0")


def test_diff_prev_day_null_when_no_previous_day_row():
    today = {"max_temperature": Decimal("20.0"), "min_temperature": Decimal("8.0")}
    result = compute_day_metrics(STATION_CODE, TARGET_DATE, today, None)
    assert result["max_temperature_diff_prev_day"] is None
    assert result["min_temperature_diff_prev_day"] is None


def test_diff_prev_day_null_when_previous_day_value_missing():
    today = {"max_temperature": Decimal("20.0"), "min_temperature": Decimal("8.0")}
    yesterday = {"max_temperature": None, "min_temperature": Decimal("5.0")}
    result = compute_day_metrics(STATION_CODE, TARGET_DATE, today, yesterday)
    assert result["max_temperature_diff_prev_day"] is None
    assert result["min_temperature_diff_prev_day"] == Decimal("3.0")


def test_rainy_day_true_when_precipitation_positive():
    assert is_rainy_day(Decimal("0.5"), "0,5") is True


def test_rainy_day_false_when_precipitation_zero():
    assert is_rainy_day(Decimal("0.0"), "0,0") is False


def test_rainy_day_true_for_trace_sentinel():
    assert is_rainy_day(None, "Ip") is True


def test_rainy_day_excluded_for_accumulated_sentinel():
    assert is_rainy_day(None, "Acum") is None


def test_rainy_day_false_when_no_precipitation_data_at_all():
    assert is_rainy_day(None, None) is False

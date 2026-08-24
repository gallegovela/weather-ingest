"""Unit tests for ingest/daily_values.py's transform().

See spec/testing.md and spec/ingest/DAILY_VALUES.md: this is exactly
the kind of fiddly parsing logic (decimal comma, sentinel values,
sparse optional fields) worth covering with unit tests, no
network/database involved.
"""

from datetime import date

from ingest.daily_values import transform

BASE_RECORD = {
    "fecha": "2024-01-01",
    "indicativo": "3195",
    "nombre": "MADRID, RETIRO",
    "provincia": "MADRID",
    "altitud": "667",
}


def test_transform_maps_station_and_date():
    result = transform({**BASE_RECORD, "tmed": "6,6"})
    assert result["station_code"] == "3195"
    assert result["date"] == date(2024, 1, 1)


def test_transform_parses_decimal_comma():
    result = transform({**BASE_RECORD, "tmed": "6,6", "tmin": "-3,8"})
    assert result["mean_temperature"] == 6.6
    assert result["min_temperature"] == -3.8


def test_transform_missing_optional_field_is_null():
    result = transform(BASE_RECORD)
    assert result["mean_temperature"] is None
    assert result["sunshine_hours"] is None


def test_transform_precipitation_plain_number():
    result = transform({**BASE_RECORD, "prec": "0,0"})
    assert result["precipitation_raw"] == "0,0"
    assert result["precipitation_mm"] == 0.0


def test_transform_precipitation_trace_sentinel():
    result = transform({**BASE_RECORD, "prec": "Ip"})
    assert result["precipitation_raw"] == "Ip"
    assert result["precipitation_mm"] is None


def test_transform_precipitation_accumulated_sentinel():
    result = transform({**BASE_RECORD, "prec": "Acum"})
    assert result["precipitation_raw"] == "Acum"
    assert result["precipitation_mm"] is None


def test_transform_precipitation_missing():
    result = transform(BASE_RECORD)
    assert result["precipitation_raw"] is None
    assert result["precipitation_mm"] is None


def test_transform_time_field_passes_through_non_time_text():
    result = transform({**BASE_RECORD, "horaHrMax": "Varias"})
    assert result["humidity_max_time"] == "Varias"


def test_transform_time_field_passes_through_plain_time():
    result = transform({**BASE_RECORD, "horatmin": "08:50"})
    assert result["min_temperature_time"] == "08:50"


def test_transform_drops_redundant_station_metadata():
    result = transform(BASE_RECORD)
    assert "nombre" not in result
    assert "provincia" not in result
    assert "altitud" not in result
    assert "indicativo" not in result

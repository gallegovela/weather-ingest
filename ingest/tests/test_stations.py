"""Unit tests for ingest/stations.py's pure transform logic.

See spec/testing.md: unit tests for pure transform/validation
functions come first, no network/database involved.
"""

from ingest.stations import parse_coordinate, transform


def test_parse_coordinate_north_east():
    assert parse_coordinate("394924N") == 39.823333
    assert parse_coordinate("025309E") == 2.885833


def test_parse_coordinate_south_west_are_negative():
    assert parse_coordinate("394924S") == -39.823333
    assert parse_coordinate("025309W") == -2.885833


def test_parse_coordinate_strips_whitespace():
    assert parse_coordinate("  394924N  ") == 39.823333


def test_transform_maps_source_fields():
    record = {
        "indicativo": "B013X",
        "nombre": " ESCORCA, LLUC ",
        "provincia": " ILLES BALEARS ",
        "latitud": "394924N",
        "longitud": "025309E",
        "altitud": "490",
        "indsinop": "",
    }

    result = transform(record)

    assert result["station_code"] == "B013X"
    assert result["name"] == "ESCORCA, LLUC"
    assert result["province"] == "ILLES BALEARS"
    assert result["altitude"] == 490
    assert result["latitude_decimal"] == 39.823333
    assert result["longitude_decimal"] == 2.885833
    assert result["synoptic_code"] is None


def test_transform_keeps_synoptic_code_when_present():
    record = {
        "indicativo": "B013X", "nombre": "X", "provincia": "X",
        "latitud": "394924N", "longitud": "025309E", "altitud": "490",
        "indsinop": "08304",
    }

    assert transform(record)["synoptic_code"] == "08304"

"""Unit tests for the climatological_values module's service-layer
delegation to the DAO -- see spec/testing.md, no real database.
"""

from modules.climatological_values import dao, service


def test_list_years_delegates_to_dao(monkeypatch):
    monkeypatch.setattr(dao, "list_years", lambda conn, station_code: [2024, 2023, 2020])

    assert service.list_years(conn=None, station_code="3195") == [2024, 2023, 2020]


def test_monthly_counts_delegates_to_dao(monkeypatch):
    captured = {}

    def fake_monthly_counts(conn, station_code, year):
        captured.update(station_code=station_code, year=year)
        return [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

    monkeypatch.setattr(dao, "monthly_counts", fake_monthly_counts)

    result = service.monthly_counts(conn=None, station_code="3195", year=2024)

    assert captured == {"station_code": "3195", "year": 2024}
    assert result == [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

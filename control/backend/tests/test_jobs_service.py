"""Unit tests for the jobs module's service-layer validation.

See spec/testing.md: unit tests for pure/service-layer logic first, no
real database -- the DAO is monkeypatched.
"""

from datetime import date

import pytest
from fastapi import HTTPException

from modules.jobs import dao, service


def test_create_daily_values_job_rejects_date_from_after_date_to():
    with pytest.raises(HTTPException) as exc_info:
        service.create_daily_values_job(
            conn=None, station_code="3195", date_from=date(2024, 4, 5), date_to=date(2024, 4, 1)
        )
    assert exc_info.value.status_code == 400


def test_create_daily_values_job_rejects_range_over_max(monkeypatch):
    monkeypatch.setattr(dao, "get_config_value", lambda conn, key: "180")

    with pytest.raises(HTTPException) as exc_info:
        service.create_daily_values_job(
            conn=None, station_code="3195", date_from=date(2020, 1, 1), date_to=date(2024, 1, 1)
        )
    assert exc_info.value.status_code == 400
    assert "180" in exc_info.value.detail


def test_create_daily_values_job_accepts_valid_range(monkeypatch):
    monkeypatch.setattr(dao, "get_config_value", lambda conn, key: "180")

    captured = {}

    def fake_create_job(conn, job_type, params):
        captured["job_type"] = job_type
        captured["params"] = params
        return (1, job_type, params, "pending", None, None, None, None, None, None)

    monkeypatch.setattr(dao, "create_job", fake_create_job)

    service.create_daily_values_job(
        conn=None, station_code="3195", date_from=date(2024, 4, 1), date_to=date(2024, 4, 5)
    )

    assert captured["job_type"] == "daily_values"
    assert captured["params"] == {
        "station_code": "3195", "date_from": "2024-04-01", "date_to": "2024-04-05",
    }


def test_cancel_job_raises_400_when_no_longer_pending(monkeypatch):
    monkeypatch.setattr(dao, "cancel_job", lambda conn, job_type, job_id: False)

    with pytest.raises(HTTPException) as exc_info:
        service.cancel_job(conn=None, job_type="stations", job_id=1)
    assert exc_info.value.status_code == 400


def test_cancel_job_succeeds_when_pending(monkeypatch):
    monkeypatch.setattr(dao, "cancel_job", lambda conn, job_type, job_id: True)

    service.cancel_job(conn=None, job_type="stations", job_id=1)  # doesn't raise


def test_delete_jobs_rejects_empty_ids():
    with pytest.raises(HTTPException) as exc_info:
        service.delete_jobs(conn=None, job_type="stations", ids=[])
    assert exc_info.value.status_code == 400


def test_delete_jobs_delegates_to_dao(monkeypatch):
    captured = {}
    monkeypatch.setattr(
        dao, "delete_jobs",
        lambda conn, job_type, ids: captured.update(job_type=job_type, ids=ids),
    )

    service.delete_jobs(conn=None, job_type="daily_values", ids=[1, 2, 3])

    assert captured == {"job_type": "daily_values", "ids": [1, 2, 3]}

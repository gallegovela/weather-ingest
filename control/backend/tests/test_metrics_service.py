"""Unit tests for the metrics module's service-layer validation and
delegation to the DAO -- see spec/testing.md, no real database.
"""

import pytest
from fastapi import HTTPException

from modules.metrics import dao, service


def test_list_metrics_rejects_page_below_one():
    with pytest.raises(HTTPException) as exc_info:
        service.list_metrics(conn=None, page=0, page_size=20, filters={})
    assert exc_info.value.status_code == 400


def test_list_metrics_rejects_page_size_below_one():
    with pytest.raises(HTTPException) as exc_info:
        service.list_metrics(conn=None, page=1, page_size=0, filters={})
    assert exc_info.value.status_code == 400


def test_list_metrics_delegates_to_dao(monkeypatch):
    captured = {}

    def fake_list_metrics(conn, page, page_size, filters):
        captured.update(page=page, page_size=page_size, filters=filters)
        return ([], 0)

    monkeypatch.setattr(dao, "list_metrics", fake_list_metrics)

    rows, total = service.list_metrics(conn=None, page=2, page_size=10, filters={"station_code": "3195"})

    assert captured == {"page": 2, "page_size": 10, "filters": {"station_code": "3195"}}
    assert rows == []
    assert total == 0

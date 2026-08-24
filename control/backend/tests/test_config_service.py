"""Unit tests for the config module's per-value_type validation.

See spec/testing.md and spec/db/tables.md (config_values, "Design
notes"): no real database -- the DAO is monkeypatched.
"""

import pytest
from fastapi import HTTPException

from modules.config import dao, service


def _row(value_type: str) -> tuple:
    return ("SOME_KEY", "old-value", value_type, "a description", None)


def test_update_value_raises_404_when_key_missing(monkeypatch):
    monkeypatch.setattr(dao, "get_value", lambda conn, key: None)

    with pytest.raises(HTTPException) as exc_info:
        service.update_value(conn=None, key="NOPE", value="x")
    assert exc_info.value.status_code == 404


@pytest.mark.parametrize("value_type", ["string", "secret"])
def test_update_value_string_like_rejects_empty(monkeypatch, value_type):
    monkeypatch.setattr(dao, "get_value", lambda conn, key: _row(value_type))

    with pytest.raises(HTTPException) as exc_info:
        service.update_value(conn=None, key="SOME_KEY", value="   ")
    assert exc_info.value.status_code == 400


@pytest.mark.parametrize("value_type", ["string", "secret"])
def test_update_value_string_like_accepts_non_empty(monkeypatch, value_type):
    monkeypatch.setattr(dao, "get_value", lambda conn, key: _row(value_type))
    monkeypatch.setattr(dao, "update_value", lambda conn, key, value: _row(value_type))

    service.update_value(conn=None, key="SOME_KEY", value="a new value")  # doesn't raise


def test_update_value_positive_integer_rejects_non_numeric(monkeypatch):
    monkeypatch.setattr(dao, "get_value", lambda conn, key: _row("positive_integer"))

    with pytest.raises(HTTPException) as exc_info:
        service.update_value(conn=None, key="SOME_KEY", value="abc")
    assert exc_info.value.status_code == 400


@pytest.mark.parametrize("value", ["0", "-5"])
def test_update_value_positive_integer_rejects_non_positive(monkeypatch, value):
    monkeypatch.setattr(dao, "get_value", lambda conn, key: _row("positive_integer"))

    with pytest.raises(HTTPException) as exc_info:
        service.update_value(conn=None, key="SOME_KEY", value=value)
    assert exc_info.value.status_code == 400


def test_update_value_positive_integer_accepts_valid(monkeypatch):
    monkeypatch.setattr(dao, "get_value", lambda conn, key: _row("positive_integer"))
    monkeypatch.setattr(dao, "update_value", lambda conn, key, value: _row("positive_integer"))

    service.update_value(conn=None, key="SOME_KEY", value="300")  # doesn't raise


def test_update_value_rejects_unknown_value_type(monkeypatch):
    monkeypatch.setattr(dao, "get_value", lambda conn, key: _row("mystery_type"))

    with pytest.raises(HTTPException) as exc_info:
        service.update_value(conn=None, key="SOME_KEY", value="anything")
    assert exc_info.value.status_code == 400

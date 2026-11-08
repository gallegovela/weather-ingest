"""Control (endpoints) layer of the metrics module.

A single read-only, filtered, paginated endpoint
(spec/control/module/metrics.md).
"""

from datetime import date

from fastapi import APIRouter, Depends
from psycopg import Connection

from core.auth import CurrentUser, get_current_user
from core.db import get_db
from core.schemas import Page
from modules.metrics import service
from modules.metrics.schemas import ClimatologicalMetricOut

router = APIRouter(prefix="/api/metrics", tags=["metrics"])


def _to_metric_out(row: tuple) -> ClimatologicalMetricOut:
    (
        station_code, name, province, metric_date,
        temperature_range, max_temperature_diff_prev_day, min_temperature_diff_prev_day,
        created_at, updated_at,
    ) = row
    return ClimatologicalMetricOut(
        station_code=station_code, name=name, province=province, date=metric_date,
        temperature_range=temperature_range,
        max_temperature_diff_prev_day=max_temperature_diff_prev_day,
        min_temperature_diff_prev_day=min_temperature_diff_prev_day,
        created_at=created_at, updated_at=updated_at,
    )


@router.get("/values", response_model=Page[ClimatologicalMetricOut])
def list_values(
    page: int = 1,
    page_size: int = 20,
    station_code: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    temperature_range_from: float | None = None,
    temperature_range_to: float | None = None,
    max_temperature_diff_prev_day_from: float | None = None,
    max_temperature_diff_prev_day_to: float | None = None,
    min_temperature_diff_prev_day_from: float | None = None,
    min_temperature_diff_prev_day_to: float | None = None,
    created_at_from: date | None = None,
    created_at_to: date | None = None,
    updated_at_from: date | None = None,
    updated_at_to: date | None = None,
    user: CurrentUser = Depends(get_current_user),
    conn: Connection = Depends(get_db),
):
    filters = {
        "station_code": station_code,
        "date_from": date_from,
        "date_to": date_to,
        "temperature_range_from": temperature_range_from,
        "temperature_range_to": temperature_range_to,
        "max_temperature_diff_prev_day_from": max_temperature_diff_prev_day_from,
        "max_temperature_diff_prev_day_to": max_temperature_diff_prev_day_to,
        "min_temperature_diff_prev_day_from": min_temperature_diff_prev_day_from,
        "min_temperature_diff_prev_day_to": min_temperature_diff_prev_day_to,
        "created_at_from": created_at_from,
        "created_at_to": created_at_to,
        "updated_at_from": updated_at_from,
        "updated_at_to": updated_at_to,
    }
    rows, total = service.list_metrics(conn, page, page_size, filters)
    return Page(
        items=[_to_metric_out(r) for r in rows], total=total, page=page, page_size=page_size
    )

"""Control (endpoints) layer of the jobs module.

One create/list/cancel/delete endpoint set per job type, instead of a
single generic /api/jobs endpoint (decided in spec/control/module/jobs.md):
each screen's request/response contract stays specific and typed. The
DAO/service still work against the single ingest_jobs table internally.
"""

from datetime import date

from fastapi import APIRouter, Depends, status
from psycopg import Connection

from core.auth import CurrentUser, get_current_user
from core.db import get_db
from core.schemas import Page
from modules.jobs import service
from modules.jobs.schemas import DailyValuesJobCreate, JobDeleteRequest, JobOut

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


def _to_job_out(row: tuple) -> JobOut:
    (
        id_, job_type, params, job_status, created_at, started_at, finished_at,
        rows_inserted, rows_updated, error_message,
    ) = row
    return JobOut(
        id=id_, job_type=job_type, params=params, status=job_status,
        created_at=created_at, started_at=started_at, finished_at=finished_at,
        rows_inserted=rows_inserted, rows_updated=rows_updated, error_message=error_message,
    )


@router.post("/stations", response_model=JobOut, status_code=status.HTTP_201_CREATED)
def create_stations_job(
    user: CurrentUser = Depends(get_current_user), conn: Connection = Depends(get_db)
):
    return _to_job_out(service.create_stations_job(conn))


@router.get("/stations", response_model=Page[JobOut])
def list_stations_jobs(
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
    created_at_from: date | None = None,
    created_at_to: date | None = None,
    user: CurrentUser = Depends(get_current_user),
    conn: Connection = Depends(get_db),
):
    filters = {"status": status, "created_at_from": created_at_from, "created_at_to": created_at_to}
    rows, total = service.list_jobs(conn, "stations", page, page_size, filters)
    return Page(items=[_to_job_out(r) for r in rows], total=total, page=page, page_size=page_size)


@router.post("/stations/{job_id}/cancel", status_code=status.HTTP_204_NO_CONTENT)
def cancel_stations_job(
    job_id: int, user: CurrentUser = Depends(get_current_user), conn: Connection = Depends(get_db)
):
    service.cancel_job(conn, "stations", job_id)


@router.delete("/stations", status_code=status.HTTP_204_NO_CONTENT)
def delete_stations_jobs(
    data: JobDeleteRequest,
    user: CurrentUser = Depends(get_current_user),
    conn: Connection = Depends(get_db),
):
    service.delete_jobs(conn, "stations", data.ids)


@router.post("/daily-values", response_model=JobOut, status_code=status.HTTP_201_CREATED)
def create_daily_values_job(
    data: DailyValuesJobCreate,
    user: CurrentUser = Depends(get_current_user),
    conn: Connection = Depends(get_db),
):
    return _to_job_out(
        service.create_daily_values_job(conn, data.station_code, data.date_from, data.date_to)
    )


@router.get("/daily-values", response_model=Page[JobOut])
def list_daily_values_jobs(
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
    created_at_from: date | None = None,
    created_at_to: date | None = None,
    station_code: str | None = None,
    user: CurrentUser = Depends(get_current_user),
    conn: Connection = Depends(get_db),
):
    filters = {
        "status": status,
        "created_at_from": created_at_from,
        "created_at_to": created_at_to,
        "station_code": station_code,
    }
    rows, total = service.list_jobs(conn, "daily_values", page, page_size, filters)
    return Page(items=[_to_job_out(r) for r in rows], total=total, page=page, page_size=page_size)


@router.post("/daily-values/{job_id}/cancel", status_code=status.HTTP_204_NO_CONTENT)
def cancel_daily_values_job(
    job_id: int, user: CurrentUser = Depends(get_current_user), conn: Connection = Depends(get_db)
):
    service.cancel_job(conn, "daily_values", job_id)


@router.delete("/daily-values", status_code=status.HTTP_204_NO_CONTENT)
def delete_daily_values_jobs(
    data: JobDeleteRequest,
    user: CurrentUser = Depends(get_current_user),
    conn: Connection = Depends(get_db),
):
    service.delete_jobs(conn, "daily_values", data.ids)

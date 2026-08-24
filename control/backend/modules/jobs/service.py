"""Service layer of the jobs module: validates params per job_type
before queuing, and the DAO's conditional-update/delete results into
HTTP errors where relevant (see spec/control/module/jobs.md).
"""

from datetime import date

from fastapi import HTTPException, status
from psycopg import Connection

from modules.jobs import dao


def create_stations_job(conn: Connection) -> tuple:
    return dao.create_job(conn, "stations", {})


def create_daily_values_job(
    conn: Connection, station_code: str, date_from: date, date_to: date
) -> tuple:
    if date_from > date_to:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "La fecha de inicio no puede ser posterior a la de fin"
        )

    max_range = int(dao.get_config_value(conn, "SCHEDULER_MAX_DATE_RANGE"))
    if (date_to - date_from).days > max_range:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"El rango no puede superar los {max_range} días",
        )

    params = {
        "station_code": station_code,
        "date_from": date_from.isoformat(),
        "date_to": date_to.isoformat(),
    }
    return dao.create_job(conn, "daily_values", params)


def list_jobs(
    conn: Connection, job_type: str, page: int, page_size: int, filters: dict
) -> tuple[list[tuple], int]:
    if page < 1:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "page must be >= 1")
    if page_size < 1:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "page_size must be >= 1")
    return dao.list_jobs(conn, job_type, page, page_size, filters)


def cancel_job(conn: Connection, job_type: str, job_id: int) -> None:
    if not dao.cancel_job(conn, job_type, job_id):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "El job ya no está pendiente")


def delete_jobs(conn: Connection, job_type: str, ids: list[int]) -> None:
    if not ids:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No se ha indicado ningún job a eliminar")
    dao.delete_jobs(conn, job_type, ids)

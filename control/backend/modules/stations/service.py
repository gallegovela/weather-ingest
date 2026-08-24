"""Service layer of the stations module: validates filter/pagination
parameters and delegates to the DAO; no additional business logic,
since it's a read-only module (spec/control/module/stations.md).
"""

from fastapi import HTTPException, status
from psycopg import Connection

from modules.stations import dao


def list_stations(
    conn: Connection, page: int, page_size: int | None, filters: dict
) -> tuple[list[tuple], int]:
    if page < 1:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "page must be >= 1")
    if page_size is not None and page_size < 1:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "page_size must be >= 1")

    return dao.list_stations(conn, page, page_size, filters)

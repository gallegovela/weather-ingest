"""Service layer of the climatological_values module: validates
filter/pagination parameters and delegates to the DAO; no additional
business logic beyond that, since it's a read-only module
(spec/control/module/climatological_values.md).
"""

from fastapi import HTTPException, status
from psycopg import Connection

from modules.climatological_values import dao


def list_values(
    conn: Connection, page: int, page_size: int, filters: dict
) -> tuple[list[tuple], int]:
    if page < 1:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "page must be >= 1")
    if page_size < 1:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "page_size must be >= 1")

    return dao.list_values(conn, page, page_size, filters)

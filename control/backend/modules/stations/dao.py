"""DAO layer of the stations module: the single access point to the
stations table (see spec/control/core.md, "Layered architecture").
Plain SQL with psycopg v3, no ORM, same criteria as ingest/.

It's a read-only module (spec/control/module/stations.md): there's no
insert/update/delete here, that's handled by ingest/stations.py.
"""

from psycopg import Connection
from psycopg.rows import tuple_row

# "Contains" filter (ILIKE), cross-cutting convention set in
# spec/control/core.md ("Paginated listings with filters").
_TEXT_CONTAINS_FIELDS = ("station_code", "name", "province", "synoptic_code", "latitude", "longitude")

# Range filter (_from/_to suffixes), same convention.
_RANGE_FIELDS = ("altitude", "latitude_decimal", "longitude_decimal", "created_at", "updated_at")

_COLUMNS = """
    station_code, name, province, latitude, longitude,
    latitude_decimal, longitude_decimal, altitude, synoptic_code,
    created_at, updated_at
"""


def _build_where(filters: dict) -> tuple[str, dict]:
    conditions = []
    params: dict = {}

    for field in _TEXT_CONTAINS_FIELDS:
        value = filters.get(field)
        if value:
            conditions.append(f"{field} ILIKE %({field})s")
            params[field] = f"%{value}%"

    for field in _RANGE_FIELDS:
        from_value = filters.get(f"{field}_from")
        if from_value is not None:
            conditions.append(f"{field} >= %({field}_from)s")
            params[f"{field}_from"] = from_value
        to_value = filters.get(f"{field}_to")
        if to_value is not None:
            conditions.append(f"{field} <= %({field}_to)s")
            params[f"{field}_to"] = to_value

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    return where, params


def list_stations(
    conn: Connection, page: int, page_size: int | None, filters: dict
) -> tuple[list[tuple], int]:
    where, params = _build_where(filters)

    with conn.cursor(row_factory=tuple_row) as cur:
        cur.execute(f"SELECT count(*) FROM stations {where}", params)
        (total,) = cur.fetchone()

        sql = f"SELECT {_COLUMNS} FROM stations {where} ORDER BY station_code"
        query_params = dict(params)
        # Without page_size: the map requests the full set without
        # pagination (decided in spec/control/module/stations.md).
        if page_size is not None:
            sql += " LIMIT %(limit)s OFFSET %(offset)s"
            query_params["limit"] = page_size
            query_params["offset"] = (page - 1) * page_size

        cur.execute(sql, query_params)
        rows = cur.fetchall()

    return rows, total

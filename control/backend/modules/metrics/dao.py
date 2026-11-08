"""DAO layer of the metrics module: the single access point to the
climatological_metrics table, joined with stations for display (see
spec/control/core.md, "Layered architecture"). Plain SQL with psycopg
v3, no ORM, same criteria as ingest/.

Read-only module (spec/control/module/metrics.md): no insert/update/
delete here, that's ingest/metrics.py's job.
"""

from psycopg import Connection
from psycopg.rows import tuple_row

# "Contains" filter (ILIKE), cross-cutting convention set in
# spec/control/core.md ("Paginated listings with filters").
_TEXT_CONTAINS_FIELDS = ("station_code",)

# Range filter (_from/_to suffixes), same convention.
_RANGE_FIELDS = (
    "date",
    "temperature_range", "max_temperature_diff_prev_day", "min_temperature_diff_prev_day",
    "created_at", "updated_at",
)

_COLUMNS = """
    cm.station_code, s.name, s.province, cm.date,
    cm.temperature_range, cm.max_temperature_diff_prev_day, cm.min_temperature_diff_prev_day,
    cm.created_at, cm.updated_at
"""

# INNER JOIN, not LEFT: station_code is a NOT NULL FK (see
# spec/db/tables.md), so every row is guaranteed a match.
_FROM = "FROM climatological_metrics cm JOIN stations s ON s.station_code = cm.station_code"


def _build_where(filters: dict) -> tuple[str, dict]:
    conditions = []
    params: dict = {}

    for field in _TEXT_CONTAINS_FIELDS:
        value = filters.get(field)
        if value:
            conditions.append(f"cm.{field} ILIKE %({field})s")
            params[field] = f"%{value}%"

    for field in _RANGE_FIELDS:
        from_value = filters.get(f"{field}_from")
        if from_value is not None:
            conditions.append(f"cm.{field} >= %({field}_from)s")
            params[f"{field}_from"] = from_value
        to_value = filters.get(f"{field}_to")
        if to_value is not None:
            conditions.append(f"cm.{field} <= %({field}_to)s")
            params[f"{field}_to"] = to_value

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    return where, params


def list_metrics(
    conn: Connection, page: int, page_size: int, filters: dict
) -> tuple[list[tuple], int]:
    where, params = _build_where(filters)

    with conn.cursor(row_factory=tuple_row) as cur:
        cur.execute(f"SELECT count(*) {_FROM} {where}", params)
        (total,) = cur.fetchone()

        sql = (
            f"SELECT {_COLUMNS} {_FROM} {where} "
            "ORDER BY cm.date DESC, cm.station_code LIMIT %(limit)s OFFSET %(offset)s"
        )
        query_params = {**params, "limit": page_size, "offset": (page - 1) * page_size}
        cur.execute(sql, query_params)
        rows = cur.fetchall()

    return rows, total

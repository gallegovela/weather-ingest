"""DAO layer of the climatological_values module: the single access
point to the climatological_values table, joined with stations for
display (see spec/control/core.md, "Layered architecture"). Plain SQL
with psycopg v3, no ORM, same criteria as ingest/.

Read-only module (spec/control/module/climatological_values.md): no
insert/update/delete here, that's ingest/daily_values.py's job.
"""

from psycopg import Connection
from psycopg.rows import tuple_row

# "Contains" filter (ILIKE), cross-cutting convention set in
# spec/control/core.md ("Paginated listings with filters"). Every
# *_time column can hold non-time text like "Varias" (see
# spec/ingest/DAILY_VALUES.md), so "contains" fits them better than an
# exact match.
_TEXT_CONTAINS_FIELDS = (
    "station_code", "precipitation_raw",
    "min_temperature_time", "max_temperature_time", "wind_gust_time",
    "pressure_max_time", "pressure_min_time",
    "humidity_max_time", "humidity_min_time",
    "precipitation_intensity_max_time",
)

# Range filter (_from/_to suffixes), same convention.
_RANGE_FIELDS = (
    "date",
    "mean_temperature", "precipitation_mm",
    "min_temperature", "max_temperature",
    "wind_gust_direction", "wind_mean_speed", "wind_gust_speed",
    "sunshine_hours",
    "pressure_max", "pressure_min",
    "humidity_mean", "humidity_max", "humidity_min",
    "precipitation_intensity_max",
    "created_at", "updated_at",
)

_COLUMNS = """
    cv.station_code, s.name, s.province, cv.date,
    cv.mean_temperature, cv.precipitation_mm, cv.precipitation_raw,
    cv.min_temperature, cv.min_temperature_time,
    cv.max_temperature, cv.max_temperature_time,
    cv.wind_gust_direction, cv.wind_mean_speed, cv.wind_gust_speed, cv.wind_gust_time,
    cv.sunshine_hours,
    cv.pressure_max, cv.pressure_max_time, cv.pressure_min, cv.pressure_min_time,
    cv.humidity_mean, cv.humidity_max, cv.humidity_max_time,
    cv.humidity_min, cv.humidity_min_time,
    cv.precipitation_intensity_max, cv.precipitation_intensity_max_time,
    cv.created_at, cv.updated_at
"""

# INNER JOIN, not LEFT: station_code is a NOT NULL FK to stations (see
# spec/db/tables.md), so every row is guaranteed a match.
_FROM = "FROM climatological_values cv JOIN stations s ON s.station_code = cv.station_code"


def _build_where(filters: dict) -> tuple[str, dict]:
    conditions = []
    params: dict = {}

    for field in _TEXT_CONTAINS_FIELDS:
        value = filters.get(field)
        if value:
            conditions.append(f"cv.{field} ILIKE %({field})s")
            params[field] = f"%{value}%"

    for field in _RANGE_FIELDS:
        from_value = filters.get(f"{field}_from")
        if from_value is not None:
            conditions.append(f"cv.{field} >= %({field}_from)s")
            params[f"{field}_from"] = from_value
        to_value = filters.get(f"{field}_to")
        if to_value is not None:
            conditions.append(f"cv.{field} <= %({field}_to)s")
            params[f"{field}_to"] = to_value

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    return where, params


def list_values(
    conn: Connection, page: int, page_size: int, filters: dict
) -> tuple[list[tuple], int]:
    where, params = _build_where(filters)

    with conn.cursor(row_factory=tuple_row) as cur:
        cur.execute(f"SELECT count(*) {_FROM} {where}", params)
        (total,) = cur.fetchone()

        sql = (
            f"SELECT {_COLUMNS} {_FROM} {where} "
            "ORDER BY cv.date DESC, cv.station_code LIMIT %(limit)s OFFSET %(offset)s"
        )
        query_params = {**params, "limit": page_size, "offset": (page - 1) * page_size}
        cur.execute(sql, query_params)
        rows = cur.fetchall()

    return rows, total


def list_years(conn: Connection, station_code: str) -> list[int]:
    """Distinct years with at least one imported row for a station,
    descending -- feeds the "Daily values chart" screen's year selector
    (spec/control/module/climatological_values.md)."""
    with conn.cursor(row_factory=tuple_row) as cur:
        cur.execute(
            "SELECT DISTINCT EXTRACT(YEAR FROM date)::int AS year "
            "FROM climatological_values WHERE station_code = %(station_code)s "
            "ORDER BY year DESC",
            {"station_code": station_code},
        )
        return [year for (year,) in cur.fetchall()]


def monthly_counts(conn: Connection, station_code: str, year: int) -> list[int]:
    """Row count per month (12 values, January first) of
    climatological_values for a station/year -- feeds chart 1 (monthly
    counts bar chart) on the "Daily values chart" screen."""
    with conn.cursor(row_factory=tuple_row) as cur:
        cur.execute(
            "SELECT EXTRACT(MONTH FROM date)::int AS month, count(*) "
            "FROM climatological_values "
            "WHERE station_code = %(station_code)s AND EXTRACT(YEAR FROM date) = %(year)s "
            "GROUP BY month",
            {"station_code": station_code, "year": year},
        )
        counts_by_month = dict(cur.fetchall())

    return [counts_by_month.get(month, 0) for month in range(1, 13)]

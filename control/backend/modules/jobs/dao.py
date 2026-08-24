"""DAO layer of the jobs module: the single access point to the
ingest_jobs table (see spec/control/core.md, "Layered architecture").
Plain SQL with psycopg v3, no ORM. Every query is scoped to a single
job_type (spec/control/module/jobs.md: "one create/list/cancel/delete
pair per job type") so the Stations screen can never touch a Daily
values row or vice versa, even though both live in the same table.
"""

from psycopg import Connection
from psycopg.rows import tuple_row
from psycopg.types.json import Jsonb

_COLUMNS = """
    id, job_type, params, status, created_at, started_at, finished_at,
    rows_inserted, rows_updated, error_message
"""


def create_job(conn: Connection, job_type: str, params: dict) -> tuple:
    with conn.cursor(row_factory=tuple_row) as cur:
        cur.execute(
            f"""
            INSERT INTO ingest_jobs (job_type, params)
            VALUES (%(job_type)s, %(params)s)
            RETURNING {_COLUMNS}
            """,
            {"job_type": job_type, "params": Jsonb(params)},
        )
        return cur.fetchone()


def _build_where(job_type: str, filters: dict) -> tuple[str, dict]:
    conditions = ["job_type = %(job_type)s"]
    params: dict = {"job_type": job_type}

    status = filters.get("status")
    if status:
        conditions.append("status = %(status)s")
        params["status"] = status

    created_at_from = filters.get("created_at_from")
    if created_at_from is not None:
        conditions.append("created_at >= %(created_at_from)s")
        params["created_at_from"] = created_at_from

    created_at_to = filters.get("created_at_to")
    if created_at_to is not None:
        conditions.append("created_at <= %(created_at_to)s")
        params["created_at_to"] = created_at_to

    # daily_values only, ignored (no matching row) for other job types.
    station_code = filters.get("station_code")
    if station_code:
        conditions.append("params ->> 'station_code' = %(station_code)s")
        params["station_code"] = station_code

    return f"WHERE {' AND '.join(conditions)}", params


def list_jobs(
    conn: Connection, job_type: str, page: int, page_size: int, filters: dict
) -> tuple[list[tuple], int]:
    where, params = _build_where(job_type, filters)

    with conn.cursor(row_factory=tuple_row) as cur:
        cur.execute(f"SELECT count(*) FROM ingest_jobs {where}", params)
        (total,) = cur.fetchone()

        sql = f"SELECT {_COLUMNS} FROM ingest_jobs {where} ORDER BY created_at DESC LIMIT %(limit)s OFFSET %(offset)s"
        query_params = {**params, "limit": page_size, "offset": (page - 1) * page_size}
        cur.execute(sql, query_params)
        rows = cur.fetchall()

    return rows, total


def cancel_job(conn: Connection, job_type: str, job_id: int) -> bool:
    # Conditional update, not check-then-update: race-safe against the
    # worker's own claim (spec/db/tables.md, ingest_jobs design notes).
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE ingest_jobs SET status = 'cancelled'
            WHERE id = %(id)s AND job_type = %(job_type)s AND status = 'pending'
            """,
            {"id": job_id, "job_type": job_type},
        )
        return cur.rowcount > 0


def delete_jobs(conn: Connection, job_type: str, ids: list[int]) -> int:
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM ingest_jobs WHERE job_type = %(job_type)s AND id = ANY(%(ids)s)",
            {"job_type": job_type, "ids": ids},
        )
        return cur.rowcount


def get_config_value(conn: Connection, key: str) -> str:
    # Same table as ingest/db.py's get_config_value, but control/backend/
    # is an independent module (own venv, spec/control/core.md) and can't
    # import ingest/ -- this is a small, deliberate duplication of a
    # 3-line query rather than a cross-module/cross-deployment import.
    with conn.cursor() as cur:
        cur.execute("SELECT value FROM config_values WHERE key = %(key)s", {"key": key})
        row = cur.fetchone()
    if row is None:
        raise RuntimeError(f"Config key {key!r} not found in config_values.")
    return row[0]

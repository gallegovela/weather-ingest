"""DAO layer of the config module: the single access point to the
config_values table (see spec/control/core.md, "Layered architecture").
Plain SQL with psycopg v3, no ORM.
"""

from psycopg import Connection
from psycopg.rows import tuple_row

_COLUMNS = "key, value, value_type, description, updated_at"


def list_values(conn: Connection) -> list[tuple]:
    with conn.cursor(row_factory=tuple_row) as cur:
        cur.execute(f"SELECT {_COLUMNS} FROM config_values ORDER BY key")
        return cur.fetchall()


def get_value(conn: Connection, key: str) -> tuple | None:
    with conn.cursor(row_factory=tuple_row) as cur:
        cur.execute(f"SELECT {_COLUMNS} FROM config_values WHERE key = %(key)s", {"key": key})
        return cur.fetchone()


def update_value(conn: Connection, key: str, value: str) -> tuple | None:
    with conn.cursor(row_factory=tuple_row) as cur:
        cur.execute(
            f"""
            UPDATE config_values SET value = %(value)s, updated_at = now()
            WHERE key = %(key)s
            RETURNING {_COLUMNS}
            """,
            {"key": key, "value": value},
        )
        return cur.fetchone()

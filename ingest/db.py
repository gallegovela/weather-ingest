"""PostgreSQL connection for the ingestion scripts.

Uses psycopg v3 directly (no SQLAlchemy), with plain SQL for the
upserts. DATABASE_URL uses the `postgresql+psycopg://` scheme
(SQLAlchemy format, see spec/db/general.md); psycopg expects a DSN
without the `+psycopg` suffix, so it's normalized here.
"""

import psycopg

from ingest.config import DATABASE_URL


def _psycopg_dsn(database_url: str) -> str:
    return database_url.replace("postgresql+psycopg://", "postgresql://", 1)


def connect() -> psycopg.Connection:
    return psycopg.connect(_psycopg_dsn(DATABASE_URL))


def get_config_value(key: str) -> str:
    """Reads a single value from config_values (see spec/db/tables.md)."""

    with connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT value FROM config_values WHERE key = %(key)s", {"key": key})
        row = cur.fetchone()

    if row is None:
        raise RuntimeError(f"Config key {key!r} not found in config_values.")
    return row[0]

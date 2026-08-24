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

"""PostgreSQL connection for control/backend/.

Same as ingest/db.py: psycopg v3 directly, no ORM, plain SQL (see
spec/db/general.md). Exposed as a FastAPI dependency: one connection
per request, committed when the request finishes without errors and
rolled back if the request fails.
"""

from collections.abc import Iterator

import psycopg

from core.config import DATABASE_URL


def _psycopg_dsn(database_url: str) -> str:
    return database_url.replace("postgresql+psycopg://", "postgresql://", 1)


def get_db() -> Iterator[psycopg.Connection]:
    conn = psycopg.connect(_psycopg_dsn(DATABASE_URL))
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

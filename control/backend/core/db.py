"""Conexión a PostgreSQL para control/backend/.

Igual que importa/db.py: psycopg v3 directo, sin ORM, SQL puro (ver
spec/db/general.md). Se expone como dependencia FastAPI: una conexión
por petición, con commit al finalizar sin errores y rollback si la
petición falla.
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

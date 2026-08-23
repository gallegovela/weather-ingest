"""Conexión a PostgreSQL para los scripts de importación.

Usa psycopg v3 directamente (sin SQLAlchemy), con SQL puro para los
upserts. DATABASE_URL usa el esquema `postgresql+psycopg://` (formato
SQLAlchemy, ver spec/db/general.md); psycopg espera un DSN sin el
sufijo `+psycopg`, así que se normaliza aquí.
"""

import psycopg

from importa.config import DATABASE_URL


def _psycopg_dsn(database_url: str) -> str:
    return database_url.replace("postgresql+psycopg://", "postgresql://", 1)


def connect() -> psycopg.Connection:
    return psycopg.connect(_psycopg_dsn(DATABASE_URL))

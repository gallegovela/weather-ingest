"""Service layer of the config module: validates a new value against
its key's value_type before saving (see spec/db/tables.md,
config_values, "Design notes"); no other business logic.
"""

from fastapi import HTTPException, status
from psycopg import Connection

from modules.config import dao


def list_values(conn: Connection) -> list[tuple]:
    return dao.list_values(conn)


def _validate(value_type: str, value: str) -> None:
    if value_type in ("string", "secret"):
        if not value.strip():
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "El valor no puede estar vacío")
        return

    if value_type == "positive_integer":
        try:
            parsed = int(value)
        except ValueError:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "El valor debe ser un número entero")
        if parsed <= 0:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "El valor debe ser un entero positivo")
        return

    raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Tipo de valor desconocido: {value_type}")


def update_value(conn: Connection, key: str, value: str) -> tuple:
    row = dao.get_value(conn, key)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Clave de configuración no encontrada")

    _, _current_value, value_type, _description, _updated_at = row
    _validate(value_type, value)

    return dao.update_value(conn, key, value)

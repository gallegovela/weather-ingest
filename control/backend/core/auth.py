"""Validación de sesión, transversal a todos los módulos.

Sesión de servidor con token opaco en cookie httpOnly/secure (ver
spec/control/core.md, sección Autenticación): sin roles, cualquier
usuario logado accede a todo el panel, así que esta dependencia es la
única barrera de acceso que necesitan los routers de cada módulo.
"""

from datetime import datetime, timedelta

from fastapi import Cookie, Depends, HTTPException, status
from psycopg import Connection

from core.config import CONTROL_SESSION_TTL_MINUTOS
from core.db import get_db

COOKIE_NAME = "control_session"

_SELECT_SESION_SQL = """
    SELECT s.control_usuario_id, s.fecha_inicio, u.login
    FROM control_sesiones s
    JOIN control_usuarios u ON u.id = s.control_usuario_id
    WHERE s.token = %(token)s
"""

_ERROR_NO_AUTENTICADO = HTTPException(status.HTTP_401_UNAUTHORIZED, "No autenticado")


class UsuarioActual:
    def __init__(self, id: int, login: str):
        self.id = id
        self.login = login


def usuario_actual(
    control_session: str | None = Cookie(default=None),
    conn: Connection = Depends(get_db),
) -> UsuarioActual:
    if not control_session:
        raise _ERROR_NO_AUTENTICADO

    with conn.cursor() as cur:
        cur.execute(_SELECT_SESION_SQL, {"token": control_session})
        fila = cur.fetchone()

    if fila is None:
        raise _ERROR_NO_AUTENTICADO

    usuario_id, fecha_inicio, login = fila
    expira = fecha_inicio + timedelta(minutes=CONTROL_SESSION_TTL_MINUTOS)
    if datetime.utcnow() >= expira:
        raise _ERROR_NO_AUTENTICADO

    return UsuarioActual(id=usuario_id, login=login)

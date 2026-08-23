"""Capa DAO del módulo seguridad: único punto de acceso a
control_usuarios y control_sesiones (ver spec/control/core.md,
"Arquitectura en capas"). SQL puro con psycopg v3, sin ORM.
"""

from datetime import date

from psycopg import Connection
from psycopg.rows import tuple_row

_SELECT_USUARIO_POR_LOGIN_SQL = """
    SELECT id, login, contrasena_hash, fecha_alta, fecha_actualizacion
    FROM control_usuarios
    WHERE login = %(login)s
"""

_INSERT_USUARIO_SQL = """
    INSERT INTO control_usuarios (login, contrasena_hash)
    VALUES (%(login)s, %(contrasena_hash)s)
    RETURNING id, login, fecha_alta, fecha_actualizacion
"""

_DELETE_USUARIO_SQL = "DELETE FROM control_usuarios WHERE id = %(id)s"

_INSERT_SESION_SQL = """
    INSERT INTO control_sesiones (token, control_usuario_id)
    VALUES (%(token)s, %(usuario_id)s)
"""

_DELETE_SESION_SQL = "DELETE FROM control_sesiones WHERE token = %(token)s"

_COLUMNAS_LISTADO = "id, login, fecha_alta, fecha_actualizacion"


def obtener_usuario_por_login(conn: Connection, login: str) -> tuple | None:
    with conn.cursor(row_factory=tuple_row) as cur:
        cur.execute(_SELECT_USUARIO_POR_LOGIN_SQL, {"login": login})
        return cur.fetchone()


def crear_usuario(conn: Connection, login: str, contrasena_hash: str) -> tuple:
    with conn.cursor(row_factory=tuple_row) as cur:
        cur.execute(_INSERT_USUARIO_SQL, {"login": login, "contrasena_hash": contrasena_hash})
        return cur.fetchone()


def actualizar_usuario(
    conn: Connection,
    usuario_id: int,
    login: str | None,
    contrasena_hash: str | None,
) -> tuple | None:
    campos = ["fecha_actualizacion = now()"]
    params: dict = {"id": usuario_id}
    if login is not None:
        campos.append("login = %(login)s")
        params["login"] = login
    if contrasena_hash is not None:
        campos.append("contrasena_hash = %(contrasena_hash)s")
        params["contrasena_hash"] = contrasena_hash

    sql = f"""
        UPDATE control_usuarios SET {', '.join(campos)}
        WHERE id = %(id)s
        RETURNING {_COLUMNAS_LISTADO}
    """
    with conn.cursor(row_factory=tuple_row) as cur:
        cur.execute(sql, params)
        return cur.fetchone()


def eliminar_usuario(conn: Connection, usuario_id: int) -> bool:
    with conn.cursor() as cur:
        cur.execute(_DELETE_USUARIO_SQL, {"id": usuario_id})
        return cur.rowcount > 0


def listar_usuarios(
    conn: Connection,
    pagina: int,
    tamano_pagina: int,
    login: str | None,
    fecha_alta_desde: date | None,
    fecha_alta_hasta: date | None,
) -> tuple[list[tuple], int]:
    condiciones = []
    params: dict = {}
    if login:
        condiciones.append("login ILIKE %(login)s")
        params["login"] = f"%{login}%"
    if fecha_alta_desde is not None:
        condiciones.append("fecha_alta >= %(fecha_alta_desde)s")
        params["fecha_alta_desde"] = fecha_alta_desde
    if fecha_alta_hasta is not None:
        condiciones.append("fecha_alta <= %(fecha_alta_hasta)s")
        params["fecha_alta_hasta"] = fecha_alta_hasta
    where = f"WHERE {' AND '.join(condiciones)}" if condiciones else ""

    with conn.cursor(row_factory=tuple_row) as cur:
        cur.execute(f"SELECT count(*) FROM control_usuarios {where}", params)
        (total,) = cur.fetchone()

        cur.execute(
            f"""
            SELECT {_COLUMNAS_LISTADO}
            FROM control_usuarios
            {where}
            ORDER BY login
            LIMIT %(limite)s OFFSET %(offset)s
            """,
            {**params, "limite": tamano_pagina, "offset": (pagina - 1) * tamano_pagina},
        )
        filas = cur.fetchall()

    return filas, total


def crear_sesion(conn: Connection, token: str, usuario_id: int) -> None:
    with conn.cursor() as cur:
        cur.execute(_INSERT_SESION_SQL, {"token": token, "usuario_id": usuario_id})


def eliminar_sesion(conn: Connection, token: str) -> None:
    with conn.cursor() as cur:
        cur.execute(_DELETE_SESION_SQL, {"token": token})

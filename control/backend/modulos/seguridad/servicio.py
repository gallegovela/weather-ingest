"""Capa de servicio del módulo seguridad: lógica de negocio (login,
gestión de usuarios); no sabe cómo se accede a los datos, delega en
el DAO (ver spec/control/core.md, "Arquitectura en capas").
"""

import secrets
from datetime import date

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import HTTPException, status
from psycopg import Connection
from psycopg.errors import UniqueViolation

from modulos.seguridad import dao

# Argon2id: algoritmo recomendado por OWASP, decidido en spec/control/core.md.
_hasher = PasswordHasher()

# Mensaje genérico decidido en spec/control/module/seguridad.md: nunca se
# indica si ha fallado el usuario o la contraseña.
_ERROR_LOGIN = HTTPException(status.HTTP_401_UNAUTHORIZED, "Error en los datos de entrada")


def login(conn: Connection, login: str, contrasena: str) -> str:
    fila = dao.obtener_usuario_por_login(conn, login)
    if fila is None:
        raise _ERROR_LOGIN

    usuario_id, _login, contrasena_hash, _fecha_alta, _fecha_actualizacion = fila
    try:
        _hasher.verify(contrasena_hash, contrasena)
    except VerifyMismatchError:
        raise _ERROR_LOGIN

    token = secrets.token_urlsafe(32)
    dao.crear_sesion(conn, token, usuario_id)
    return token


def logout(conn: Connection, token: str) -> None:
    dao.eliminar_sesion(conn, token)


def listar_usuarios(
    conn: Connection,
    pagina: int,
    tamano_pagina: int,
    login: str | None,
    fecha_alta_desde: date | None,
    fecha_alta_hasta: date | None,
) -> tuple[list[tuple], int]:
    return dao.listar_usuarios(conn, pagina, tamano_pagina, login, fecha_alta_desde, fecha_alta_hasta)


def crear_usuario(conn: Connection, login: str, contrasena: str) -> tuple:
    contrasena_hash = _hasher.hash(contrasena)
    try:
        return dao.crear_usuario(conn, login, contrasena_hash)
    except UniqueViolation:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Ya existe un usuario con ese login")


def editar_usuario(
    conn: Connection,
    usuario_id: int,
    login: str | None,
    contrasena: str | None,
) -> tuple:
    contrasena_hash = _hasher.hash(contrasena) if contrasena else None
    try:
        fila = dao.actualizar_usuario(conn, usuario_id, login=login, contrasena_hash=contrasena_hash)
    except UniqueViolation:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Ya existe un usuario con ese login")
    if fila is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario no encontrado")
    return fila


def eliminar_usuario(conn: Connection, usuario_id: int, usuario_actual_id: int) -> None:
    # Decidido en spec/control/module/seguridad.md: un usuario no puede
    # eliminarse a sí mismo.
    if usuario_id == usuario_actual_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No puedes eliminar tu propio usuario")
    if not dao.eliminar_usuario(conn, usuario_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario no encontrado")

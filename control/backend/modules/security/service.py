"""Service layer of the security module: business logic (login, user
management); doesn't know how data is accessed, delegates to the DAO
(see spec/control/core.md, "Layered architecture").
"""

import secrets
from datetime import date

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import HTTPException, status
from psycopg import Connection
from psycopg.errors import UniqueViolation

from modules.security import dao

# Argon2id: algorithm recommended by OWASP, decided in spec/control/core.md.
_hasher = PasswordHasher()

# Generic message decided in spec/control/module/security.md: never
# indicates whether the username or the password failed.
_ERROR_LOGIN = HTTPException(status.HTTP_401_UNAUTHORIZED, "Error en los datos de entrada")


def login(conn: Connection, login: str, password: str) -> str:
    row = dao.get_user_by_login(conn, login)
    if row is None:
        raise _ERROR_LOGIN

    user_id, _login, password_hash, _created_at, _updated_at = row
    try:
        _hasher.verify(password_hash, password)
    except VerifyMismatchError:
        raise _ERROR_LOGIN

    token = secrets.token_urlsafe(32)
    dao.create_session(conn, token, user_id)
    return token


def logout(conn: Connection, token: str) -> None:
    dao.delete_session(conn, token)


def list_users(
    conn: Connection,
    page: int,
    page_size: int,
    login: str | None,
    created_at_from: date | None,
    created_at_to: date | None,
) -> tuple[list[tuple], int]:
    return dao.list_users(conn, page, page_size, login, created_at_from, created_at_to)


def create_user(conn: Connection, login: str, password: str) -> tuple:
    password_hash = _hasher.hash(password)
    try:
        return dao.create_user(conn, login, password_hash)
    except UniqueViolation:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Ya existe un usuario con ese login")


def update_user(
    conn: Connection,
    user_id: int,
    login: str | None,
    password: str | None,
) -> tuple:
    password_hash = _hasher.hash(password) if password else None
    try:
        row = dao.update_user(conn, user_id, login=login, password_hash=password_hash)
    except UniqueViolation:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Ya existe un usuario con ese login")
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario no encontrado")
    return row


def delete_user(conn: Connection, user_id: int, current_user_id: int) -> None:
    # Decided in spec/control/module/security.md: a user can't delete
    # themself.
    if user_id == current_user_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No puedes eliminar tu propio usuario")
    if not dao.delete_user(conn, user_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario no encontrado")

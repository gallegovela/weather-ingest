"""Session validation, cross-cutting to every module.

Server-side session with an opaque token in an httpOnly/secure cookie
(see spec/control/core.md, Authentication section): no roles, any
logged-in user accesses the whole panel, so this dependency is the
only access barrier each module's routers need.
"""

from datetime import datetime, timedelta

from fastapi import Cookie, Depends, HTTPException, status
from psycopg import Connection

from core.config import CONTROL_SESSION_TTL_MINUTES
from core.db import get_db

COOKIE_NAME = "control_session"

_SELECT_SESSION_SQL = """
    SELECT s.user_id, s.started_at, u.login
    FROM control_sessions s
    JOIN control_users u ON u.id = s.user_id
    WHERE s.token = %(token)s
"""

_ERROR_NOT_AUTHENTICATED = HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")


class CurrentUser:
    def __init__(self, id: int, login: str):
        self.id = id
        self.login = login


def get_current_user(
    control_session: str | None = Cookie(default=None),
    conn: Connection = Depends(get_db),
) -> CurrentUser:
    if not control_session:
        raise _ERROR_NOT_AUTHENTICATED

    with conn.cursor() as cur:
        cur.execute(_SELECT_SESSION_SQL, {"token": control_session})
        row = cur.fetchone()

    if row is None:
        raise _ERROR_NOT_AUTHENTICATED

    user_id, started_at, login = row
    expires = started_at + timedelta(minutes=CONTROL_SESSION_TTL_MINUTES)
    if datetime.utcnow() >= expires:
        raise _ERROR_NOT_AUTHENTICATED

    return CurrentUser(id=user_id, login=login)

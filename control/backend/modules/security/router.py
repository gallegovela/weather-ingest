"""Control (endpoints) layer of the security module.

Routes under /api/security, following the cross-cutting REST contract
from spec/control/core.md.
"""

from datetime import date

from fastapi import APIRouter, Cookie, Depends, Response, status
from psycopg import Connection

from core.auth import COOKIE_NAME, CurrentUser, get_current_user
from core.db import get_db
from core.schemas import Page
from modules.security import service
from modules.security.schemas import LoginRequest, SessionOut, UserCreate, UserOut, UserUpdate

router = APIRouter(prefix="/api/security", tags=["security"])


def _to_user_out(row: tuple) -> UserOut:
    return UserOut(id=row[0], login=row[1], created_at=row[2], updated_at=row[3])


@router.post("/login")
def login(data: LoginRequest, response: Response, conn: Connection = Depends(get_db)):
    token = service.login(conn, data.login, data.password)
    response.set_cookie(COOKIE_NAME, token, httponly=True, secure=True, samesite="lax")
    return {"detail": "ok"}


@router.post("/logout")
def logout(
    response: Response,
    control_session: str | None = Cookie(default=None),
    user: CurrentUser = Depends(get_current_user),
    conn: Connection = Depends(get_db),
):
    if control_session:
        service.logout(conn, control_session)
    response.delete_cookie(COOKIE_NAME)
    return {"detail": "ok"}


@router.get("/session", response_model=SessionOut)
def get_session(user: CurrentUser = Depends(get_current_user)):
    # Used by control/frontend/ as a session guard (is there a valid
    # session?) and to know the logged-in user's id (hide "delete" on
    # oneself, see spec/control/module/security.md).
    return SessionOut(id=user.id, login=user.login)


@router.get("/users", response_model=Page[UserOut])
def list_users(
    page: int = 1,
    page_size: int = 20,
    login: str | None = None,
    created_at_from: date | None = None,
    created_at_to: date | None = None,
    user: CurrentUser = Depends(get_current_user),
    conn: Connection = Depends(get_db),
):
    rows, total = service.list_users(
        conn, page, page_size, login, created_at_from, created_at_to
    )
    return Page(
        items=[_to_user_out(r) for r in rows], total=total, page=page, page_size=page_size
    )


@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    data: UserCreate,
    user: CurrentUser = Depends(get_current_user),
    conn: Connection = Depends(get_db),
):
    return _to_user_out(service.create_user(conn, data.login, data.password))


@router.put("/users/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    data: UserUpdate,
    user: CurrentUser = Depends(get_current_user),
    conn: Connection = Depends(get_db),
):
    return _to_user_out(
        service.update_user(conn, user_id, login=data.login, password=data.password)
    )


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    user: CurrentUser = Depends(get_current_user),
    conn: Connection = Depends(get_db),
):
    service.delete_user(conn, user_id, user.id)

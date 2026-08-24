"""DAO layer of the security module: the single access point to
control_users and control_sessions (see spec/control/core.md,
"Layered architecture"). Plain SQL with psycopg v3, no ORM.
"""

from datetime import date

from psycopg import Connection
from psycopg.rows import tuple_row

_SELECT_USER_BY_LOGIN_SQL = """
    SELECT id, login, password_hash, created_at, updated_at
    FROM control_users
    WHERE login = %(login)s
"""

_INSERT_USER_SQL = """
    INSERT INTO control_users (login, password_hash)
    VALUES (%(login)s, %(password_hash)s)
    RETURNING id, login, created_at, updated_at
"""

_DELETE_USER_SQL = "DELETE FROM control_users WHERE id = %(id)s"

_INSERT_SESSION_SQL = """
    INSERT INTO control_sessions (token, user_id)
    VALUES (%(token)s, %(user_id)s)
"""

_DELETE_SESSION_SQL = "DELETE FROM control_sessions WHERE token = %(token)s"

_LIST_COLUMNS = "id, login, created_at, updated_at"


def get_user_by_login(conn: Connection, login: str) -> tuple | None:
    with conn.cursor(row_factory=tuple_row) as cur:
        cur.execute(_SELECT_USER_BY_LOGIN_SQL, {"login": login})
        return cur.fetchone()


def create_user(conn: Connection, login: str, password_hash: str) -> tuple:
    with conn.cursor(row_factory=tuple_row) as cur:
        cur.execute(_INSERT_USER_SQL, {"login": login, "password_hash": password_hash})
        return cur.fetchone()


def update_user(
    conn: Connection,
    user_id: int,
    login: str | None,
    password_hash: str | None,
) -> tuple | None:
    fields = ["updated_at = now()"]
    params: dict = {"id": user_id}
    if login is not None:
        fields.append("login = %(login)s")
        params["login"] = login
    if password_hash is not None:
        fields.append("password_hash = %(password_hash)s")
        params["password_hash"] = password_hash

    sql = f"""
        UPDATE control_users SET {', '.join(fields)}
        WHERE id = %(id)s
        RETURNING {_LIST_COLUMNS}
    """
    with conn.cursor(row_factory=tuple_row) as cur:
        cur.execute(sql, params)
        return cur.fetchone()


def delete_user(conn: Connection, user_id: int) -> bool:
    with conn.cursor() as cur:
        cur.execute(_DELETE_USER_SQL, {"id": user_id})
        return cur.rowcount > 0


def list_users(
    conn: Connection,
    page: int,
    page_size: int,
    login: str | None,
    created_at_from: date | None,
    created_at_to: date | None,
) -> tuple[list[tuple], int]:
    conditions = []
    params: dict = {}
    if login:
        conditions.append("login ILIKE %(login)s")
        params["login"] = f"%{login}%"
    if created_at_from is not None:
        conditions.append("created_at >= %(created_at_from)s")
        params["created_at_from"] = created_at_from
    if created_at_to is not None:
        conditions.append("created_at <= %(created_at_to)s")
        params["created_at_to"] = created_at_to
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    with conn.cursor(row_factory=tuple_row) as cur:
        cur.execute(f"SELECT count(*) FROM control_users {where}", params)
        (total,) = cur.fetchone()

        cur.execute(
            f"""
            SELECT {_LIST_COLUMNS}
            FROM control_users
            {where}
            ORDER BY login
            LIMIT %(limit)s OFFSET %(offset)s
            """,
            {**params, "limit": page_size, "offset": (page - 1) * page_size},
        )
        rows = cur.fetchall()

    return rows, total


def create_session(conn: Connection, token: str, user_id: int) -> None:
    with conn.cursor() as cur:
        cur.execute(_INSERT_SESSION_SQL, {"token": token, "user_id": user_id})


def delete_session(conn: Connection, token: str) -> None:
    with conn.cursor() as cur:
        cur.execute(_DELETE_SESSION_SQL, {"token": token})

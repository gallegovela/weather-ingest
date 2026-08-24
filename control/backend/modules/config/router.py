"""Control (endpoints) layer of the config module.

Routes under /api/config, following the cross-cutting REST contract
from spec/control/core.md -- except pagination, deliberately not used
here (spec/control/module/config.md: the expected number of keys is
small enough to return in one call).
"""

from fastapi import APIRouter, Depends
from psycopg import Connection

from core.auth import CurrentUser, get_current_user
from core.db import get_db
from modules.config import service
from modules.config.schemas import ConfigValueOut, ConfigValueUpdate

router = APIRouter(prefix="/api/config", tags=["config"])

# Never sent over the wire for value_type == "secret" -- masked instead
# (see spec/db/tables.md, config_values, "secret"). A fixed placeholder,
# not derived from the real value's length, so it doesn't leak that either.
_SECRET_MASK = "••••••••"


def _to_value_out(row: tuple) -> ConfigValueOut:
    key, value, value_type, description, updated_at = row
    return ConfigValueOut(
        key=key,
        value=_SECRET_MASK if value_type == "secret" else value,
        value_type=value_type,
        description=description,
        updated_at=updated_at,
    )


@router.get("/values", response_model=list[ConfigValueOut])
def list_values(user: CurrentUser = Depends(get_current_user), conn: Connection = Depends(get_db)):
    return [_to_value_out(r) for r in service.list_values(conn)]


@router.put("/values/{key}", response_model=ConfigValueOut)
def update_value(
    key: str,
    data: ConfigValueUpdate,
    user: CurrentUser = Depends(get_current_user),
    conn: Connection = Depends(get_db),
):
    return _to_value_out(service.update_value(conn, key, data.value))

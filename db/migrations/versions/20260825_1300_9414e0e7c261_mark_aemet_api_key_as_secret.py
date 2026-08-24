"""mark_aemet_api_key_as_secret

Revision ID: 9414e0e7c261
Revises: 48dd1a013763
Create Date: 2026-08-25 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9414e0e7c261'
down_revision: Union[str, None] = '48dd1a013763'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# New value_type, distinct from 'string': the config module masks its
# value in GET responses instead of returning it in plain text (see
# spec/db/tables.md, config_values, and spec/control/module/config.md).
# No schema change needed -- value_type isn't DB-enforced (no CHECK).


def upgrade() -> None:
    op.execute("UPDATE config_values SET value_type = 'secret' WHERE key = 'AEMET_API_KEY'")


def downgrade() -> None:
    op.execute("UPDATE config_values SET value_type = 'string' WHERE key = 'AEMET_API_KEY'")

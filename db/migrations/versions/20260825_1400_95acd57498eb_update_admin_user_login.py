"""update_admin_user_login

Revision ID: 95acd57498eb
Revises: 9414e0e7c261
Create Date: 2026-08-25 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '95acd57498eb'
down_revision: Union[str, None] = '9414e0e7c261'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# The original seed (create_control_admin_user) used admin@weather.local,
# which pydantic's EmailStr rejects outright (.local is a reserved TLD,
# a syntax rule, not a deliverability/DNS check) -- the seeded admin
# could never actually log in through the real API. Password unchanged
# (still "admin", see spec/db/tables.md).
OLD_LOGIN = "admin@weather.local"
NEW_LOGIN = "info@gallegovela.es"


def upgrade() -> None:
    op.execute(
        f"UPDATE control_users SET login = '{NEW_LOGIN}', updated_at = now() "
        f"WHERE login = '{OLD_LOGIN}'"
    )


def downgrade() -> None:
    op.execute(
        f"UPDATE control_users SET login = '{OLD_LOGIN}', updated_at = now() "
        f"WHERE login = '{NEW_LOGIN}'"
    )

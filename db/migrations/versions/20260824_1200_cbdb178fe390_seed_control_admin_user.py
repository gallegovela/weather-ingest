"""seed_control_admin_user

Revision ID: cbdb178fe390
Revises: d338051e8b13
Create Date: 2026-08-24 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cbdb178fe390'
down_revision: Union[str, None] = 'd338051e8b13'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Default admin user, seeded so there's always a way to log into the
# control panel after rebuilding the database from scratch (control_users
# starts empty, and there's no self-service signup — see
# spec/control/module/security.md). Password hash below is Argon2id
# (spec/control/core.md) for the default password "admin"; change it after
# first login.
ADMIN_LOGIN = "admin@weather.local"
ADMIN_PASSWORD_HASH = "$argon2id$v=19$m=65536,t=3,p=4$J/EEoh/LbCgomTvfZM8k8w$4SJ+mSEplCGGybgjZ8qwTRlPTKgyl7NbfD+c5RS6T1w"


def upgrade() -> None:
    op.execute(
        f"""
        INSERT INTO control_users (login, password_hash)
        VALUES ('{ADMIN_LOGIN}', '{ADMIN_PASSWORD_HASH}')
        """
    )


def downgrade() -> None:
    op.execute(f"DELETE FROM control_users WHERE login = '{ADMIN_LOGIN}'")

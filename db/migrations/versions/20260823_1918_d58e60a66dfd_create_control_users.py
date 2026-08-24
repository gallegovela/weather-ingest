"""create_control_users

Revision ID: d58e60a66dfd
Revises: 8605ecc0b9f7
Create Date: 2026-08-23 19:18:01.280944

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd58e60a66dfd'
down_revision: Union[str, None] = '8605ecc0b9f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE control_users (
            id                  bigint GENERATED ALWAYS AS IDENTITY,
            login               varchar     NOT NULL,
            password_hash       varchar     NOT NULL,
            created_at          timestamp   NOT NULL DEFAULT now(),
            updated_at          timestamp   NOT NULL DEFAULT now(),
            CONSTRAINT pk_control_users PRIMARY KEY (id),
            CONSTRAINT uq_control_users_login UNIQUE (login)
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE control_users")

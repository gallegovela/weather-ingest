"""create_control_sessions

Revision ID: d338051e8b13
Revises: d58e60a66dfd
Create Date: 2026-08-23 19:18:15.700997

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd338051e8b13'
down_revision: Union[str, None] = 'd58e60a66dfd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE control_sessions (
            token               varchar     NOT NULL,
            user_id             bigint      NOT NULL,
            started_at          timestamp   NOT NULL DEFAULT now(),
            CONSTRAINT pk_control_sessions PRIMARY KEY (token),
            CONSTRAINT fk_control_sessions_control_users
                FOREIGN KEY (user_id) REFERENCES control_users (id)
                ON DELETE CASCADE
        )
        """
    )
    op.execute(
        """
        CREATE INDEX ix_control_sessions_user_id
            ON control_sessions (user_id)
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE control_sessions")

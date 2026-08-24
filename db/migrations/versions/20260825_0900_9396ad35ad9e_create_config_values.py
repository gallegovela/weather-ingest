"""create_config_values

Revision ID: 9396ad35ad9e
Revises: cbdb178fe390
Create Date: 2026-08-25 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9396ad35ad9e'
down_revision: Union[str, None] = 'cbdb178fe390'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE config_values (
            key         varchar     NOT NULL,
            value       varchar     NOT NULL,
            description varchar     NOT NULL,
            updated_at  timestamp   NOT NULL DEFAULT now(),
            CONSTRAINT pk_config_values PRIMARY KEY (key)
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE config_values")

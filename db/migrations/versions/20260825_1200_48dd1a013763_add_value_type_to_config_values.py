"""add_value_type_to_config_values

Revision ID: 48dd1a013763
Revises: ed154b6125de
Create Date: 2026-08-25 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '48dd1a013763'
down_revision: Union[str, None] = 'ed154b6125de'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE config_values ADD COLUMN value_type varchar")
    op.execute(
        "UPDATE config_values SET value_type = 'string' WHERE key = 'AEMET_API_KEY'"
    )
    op.execute(
        """
        UPDATE config_values SET value_type = 'positive_integer'
        WHERE key IN ('POLL_INTERVAL_SECONDS', 'SCHEDULER_MAX_DATE_RANGE')
        """
    )
    op.execute("ALTER TABLE config_values ALTER COLUMN value_type SET NOT NULL")


def downgrade() -> None:
    op.execute("ALTER TABLE config_values DROP COLUMN value_type")

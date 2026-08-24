"""seed_config_value_poll_interval_seconds

Revision ID: 2e1257b427e2
Revises: 789f43178853
Create Date: 2026-08-25 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2e1257b427e2'
down_revision: Union[str, None] = '789f43178853'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

CONFIG_KEY = "POLL_INTERVAL_SECONDS"
VALUE = "300"
DESCRIPTION = (
    "Seconds the ingest job worker sleeps between poll iterations when "
    "there is no pending job (see spec/ingest/general.md)."
)


def upgrade() -> None:
    op.execute(
        f"""
        INSERT INTO config_values (key, value, description)
        VALUES ('{CONFIG_KEY}', '{VALUE}', '{DESCRIPTION}')
        """
    )


def downgrade() -> None:
    op.execute(f"DELETE FROM config_values WHERE key = '{CONFIG_KEY}'")

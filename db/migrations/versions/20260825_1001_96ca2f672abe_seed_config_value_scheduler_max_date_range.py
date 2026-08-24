"""seed_config_value_scheduler_max_date_range

Revision ID: 96ca2f672abe
Revises: 2e1257b427e2
Create Date: 2026-08-25 10:01:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '96ca2f672abe'
down_revision: Union[str, None] = '2e1257b427e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

CONFIG_KEY = "SCHEDULER_MAX_DATE_RANGE"
VALUE = "180"
DESCRIPTION = (
    "Maximum number of days a single daily_values ingest job may span. "
    "Longer ranges are split into several jobs from the Jobs module "
    "(see spec/control/module/jobs.md and spec/ingest/DAILY_VALUES.md)."
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

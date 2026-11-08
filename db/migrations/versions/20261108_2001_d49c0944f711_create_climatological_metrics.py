"""create_climatological_metrics

Revision ID: d49c0944f711
Revises: 51b6c3fb5052
Create Date: 2026-11-08 20:01:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd49c0944f711'
down_revision: Union[str, None] = '51b6c3fb5052'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE climatological_metrics (
            station_code                      varchar     NOT NULL,
            date                               date        NOT NULL,
            temperature_range                  numeric,
            max_temperature_diff_prev_day      numeric,
            min_temperature_diff_prev_day      numeric,
            created_at                         timestamp   NOT NULL DEFAULT now(),
            updated_at                         timestamp   NOT NULL DEFAULT now(),
            CONSTRAINT pk_climatological_metrics PRIMARY KEY (station_code, date),
            CONSTRAINT fk_climatological_metrics_climatological_values
                FOREIGN KEY (station_code, date) REFERENCES climatological_values (station_code, date)
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE climatological_metrics")

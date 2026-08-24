"""create_stations

Revision ID: f54155bc39b7
Revises:
Create Date: 2026-08-22 20:51:16.851017

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f54155bc39b7'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE stations (
            station_code        varchar     NOT NULL,
            name                varchar     NOT NULL,
            province            varchar     NOT NULL,
            latitude            varchar     NOT NULL,
            longitude           varchar     NOT NULL,
            latitude_decimal    numeric(9,6) NOT NULL,
            longitude_decimal   numeric(9,6) NOT NULL,
            altitude            integer     NOT NULL,
            synoptic_code       varchar,
            created_at          timestamp   NOT NULL DEFAULT now(),
            updated_at          timestamp   NOT NULL DEFAULT now(),
            CONSTRAINT pk_stations PRIMARY KEY (station_code)
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE stations")

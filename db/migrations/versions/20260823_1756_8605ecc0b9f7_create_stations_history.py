"""create_stations_history

Revision ID: 8605ecc0b9f7
Revises: f54155bc39b7
Create Date: 2026-08-23 17:56:02.647183

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8605ecc0b9f7'
down_revision: Union[str, None] = 'f54155bc39b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE stations_history (
            id                  bigint GENERATED ALWAYS AS IDENTITY,
            station_code        varchar     NOT NULL,
            name                varchar     NOT NULL,
            province            varchar     NOT NULL,
            latitude            varchar     NOT NULL,
            longitude           varchar     NOT NULL,
            latitude_decimal    numeric(9,6) NOT NULL,
            longitude_decimal   numeric(9,6) NOT NULL,
            altitude            integer     NOT NULL,
            synoptic_code       varchar,
            changed_at          timestamp   NOT NULL,
            CONSTRAINT pk_stations_history PRIMARY KEY (id),
            CONSTRAINT fk_stations_history_stations
                FOREIGN KEY (station_code) REFERENCES stations (station_code)
        )
        """
    )
    op.execute(
        """
        CREATE INDEX ix_stations_history_station_code
            ON stations_history (station_code)
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE stations_history")

"""create_climatological_values

Revision ID: ed154b6125de
Revises: deb09b15850e
Create Date: 2026-08-25 11:01:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ed154b6125de'
down_revision: Union[str, None] = 'deb09b15850e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE climatological_values (
            station_code                      varchar     NOT NULL,
            date                               date        NOT NULL,
            mean_temperature                   numeric,
            precipitation_mm                   numeric,
            precipitation_raw                  varchar,
            min_temperature                    numeric,
            min_temperature_time               varchar,
            max_temperature                    numeric,
            max_temperature_time               varchar,
            wind_gust_direction                numeric,
            wind_mean_speed                    numeric,
            wind_gust_speed                    numeric,
            wind_gust_time                     varchar,
            sunshine_hours                     numeric,
            pressure_max                       numeric,
            pressure_max_time                  varchar,
            pressure_min                       numeric,
            pressure_min_time                  varchar,
            humidity_mean                      numeric,
            humidity_max                       numeric,
            humidity_max_time                  varchar,
            humidity_min                       numeric,
            humidity_min_time                  varchar,
            precipitation_intensity_max        numeric,
            precipitation_intensity_max_time   varchar,
            created_at                         timestamp   NOT NULL DEFAULT now(),
            updated_at                         timestamp   NOT NULL DEFAULT now(),
            CONSTRAINT pk_climatological_values PRIMARY KEY (station_code, date),
            CONSTRAINT fk_climatological_values_stations
                FOREIGN KEY (station_code) REFERENCES stations (station_code)
        )
        """
    )
    op.execute("CREATE INDEX ix_climatological_values_date ON climatological_values (date)")


def downgrade() -> None:
    op.execute("DROP TABLE climatological_values")

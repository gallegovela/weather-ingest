"""create_estaciones_historico

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
        CREATE TABLE estaciones_historico (
            id                  bigint GENERATED ALWAYS AS IDENTITY,
            estacion_indicativo varchar     NOT NULL,
            nombre              varchar     NOT NULL,
            provincia           varchar     NOT NULL,
            latitud             varchar     NOT NULL,
            longitud            varchar     NOT NULL,
            latitud_decimal     numeric(9,6) NOT NULL,
            longitud_decimal    numeric(9,6) NOT NULL,
            altitud             integer     NOT NULL,
            indsinop            varchar,
            fecha_cambio        timestamp   NOT NULL,
            CONSTRAINT pk_estaciones_historico PRIMARY KEY (id),
            CONSTRAINT fk_estaciones_historico_estaciones
                FOREIGN KEY (estacion_indicativo) REFERENCES estaciones (indicativo)
        )
        """
    )
    op.execute(
        """
        CREATE INDEX ix_estaciones_historico_estacion_indicativo
            ON estaciones_historico (estacion_indicativo)
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE estaciones_historico")

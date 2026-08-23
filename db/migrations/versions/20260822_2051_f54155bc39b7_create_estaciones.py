"""create_estaciones

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
        CREATE TABLE estaciones (
            indicativo          varchar     NOT NULL,
            nombre              varchar     NOT NULL,
            provincia           varchar     NOT NULL,
            latitud             varchar     NOT NULL,
            longitud            varchar     NOT NULL,
            latitud_decimal     numeric(9,6) NOT NULL,
            longitud_decimal    numeric(9,6) NOT NULL,
            altitud             integer     NOT NULL,
            indsinop            varchar,
            fecha_alta          timestamp   NOT NULL DEFAULT now(),
            fecha_actualizacion timestamp   NOT NULL DEFAULT now(),
            CONSTRAINT pk_estaciones PRIMARY KEY (indicativo)
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE estaciones")

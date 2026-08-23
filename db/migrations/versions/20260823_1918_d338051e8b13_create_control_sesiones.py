"""create_control_sesiones

Revision ID: d338051e8b13
Revises: d58e60a66dfd
Create Date: 2026-08-23 19:18:15.700997

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd338051e8b13'
down_revision: Union[str, None] = 'd58e60a66dfd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE control_sesiones (
            token               varchar     NOT NULL,
            control_usuario_id  bigint      NOT NULL,
            fecha_inicio        timestamp   NOT NULL DEFAULT now(),
            CONSTRAINT pk_control_sesiones PRIMARY KEY (token),
            CONSTRAINT fk_control_sesiones_control_usuarios
                FOREIGN KEY (control_usuario_id) REFERENCES control_usuarios (id)
                ON DELETE CASCADE
        )
        """
    )
    op.execute(
        """
        CREATE INDEX ix_control_sesiones_control_usuario_id
            ON control_sesiones (control_usuario_id)
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE control_sesiones")

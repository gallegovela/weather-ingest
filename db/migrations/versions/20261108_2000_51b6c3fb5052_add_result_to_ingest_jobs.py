"""add_result_to_ingest_jobs

Revision ID: 51b6c3fb5052
Revises: 95acd57498eb
Create Date: 2026-11-08 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '51b6c3fb5052'
down_revision: Union[str, None] = '95acd57498eb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE ingest_jobs ADD COLUMN result jsonb")


def downgrade() -> None:
    op.execute("ALTER TABLE ingest_jobs DROP COLUMN result")

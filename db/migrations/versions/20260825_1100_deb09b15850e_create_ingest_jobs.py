"""create_ingest_jobs

Revision ID: deb09b15850e
Revises: 96ca2f672abe
Create Date: 2026-08-25 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'deb09b15850e'
down_revision: Union[str, None] = '96ca2f672abe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE ingest_jobs (
            id             bigint GENERATED ALWAYS AS IDENTITY,
            job_type       varchar     NOT NULL,
            params         jsonb       NOT NULL,
            status         varchar     NOT NULL DEFAULT 'pending',
            created_at     timestamp   NOT NULL DEFAULT now(),
            started_at     timestamp,
            finished_at    timestamp,
            rows_inserted  integer,
            rows_updated   integer,
            error_message  varchar,
            CONSTRAINT pk_ingest_jobs PRIMARY KEY (id)
        )
        """
    )
    op.execute("CREATE INDEX ix_ingest_jobs_status ON ingest_jobs (status)")
    op.execute("CREATE INDEX ix_ingest_jobs_job_type ON ingest_jobs (job_type)")


def downgrade() -> None:
    op.execute("DROP TABLE ingest_jobs")

"""seed_config_value_aemet_api_key

Revision ID: 789f43178853
Revises: 9396ad35ad9e
Create Date: 2026-08-25 09:01:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '789f43178853'
down_revision: Union[str, None] = '9396ad35ad9e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Seeded with a placeholder, not the real key: this migration is
# version-controlled, and the actual AEMET_API_KEY is a secret tied to
# a real account (see spec/db/tables.md, table config_values). Set the
# real value with a direct UPDATE against config_values after applying
# this migration, same as the value already in .env today.
CONFIG_KEY = "AEMET_API_KEY"
PLACEHOLDER_VALUE = "CHANGE_ME"
DESCRIPTION = "AEMET OpenData API key, sent as the api_key header on every request to opendata.aemet.es."


def upgrade() -> None:
    op.execute(
        f"""
        INSERT INTO config_values (key, value, description)
        VALUES ('{CONFIG_KEY}', '{PLACEHOLDER_VALUE}', '{DESCRIPTION}')
        """
    )


def downgrade() -> None:
    op.execute(f"DELETE FROM config_values WHERE key = '{CONFIG_KEY}'")

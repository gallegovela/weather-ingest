"""Configuration loading shared by the ingestion scripts.

Reads the project root's .env (same file db/ uses, see
spec/db/general.md), independent of the rest of the app.

AEMET_API_KEY is *not* read here: it lives in the config_values table
(see spec/db/tables.md and ingest/db.py's get_config_value), not .env.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(
            f"{name} is not set. Add it to the .env file at the project root."
        )
    return value


DATABASE_URL = _require_env("DATABASE_URL")

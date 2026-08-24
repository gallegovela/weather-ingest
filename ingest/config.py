"""Configuration loading shared by the ingestion scripts.

Reads the project root's .env (same file db/ uses, see
spec/db/general.md), independent of the rest of the app.
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


AEMET_API_KEY = _require_env("AEMET_API_KEY")
DATABASE_URL = _require_env("DATABASE_URL")

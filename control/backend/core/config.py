"""Configuration loading for control/backend/.

Reuses the project root's .env (same file used by db/ and ingest/,
see spec/db/general.md), independently from the rest of the app (own
virtual environment, see spec/control/core.md).
"""

import os
from pathlib import Path

from dotenv import load_dotenv

try:
    # In local development (venv), config.py lives in
    # control/backend/core/ inside the full repo, so going up 3
    # levels reaches the project root where .env is.
    PROJECT_ROOT = Path(__file__).resolve().parents[3]
    load_dotenv(PROJECT_ROOT / ".env")
except IndexError:
    # In the Docker container only control/backend/ is copied (see
    # Dockerfile), so that directory depth doesn't exist. That's fine:
    # docker-compose.yml already injects the environment variables
    # directly, no .env needs to be read.
    pass


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(
            f"{name} is not set. Add it to the .env file at the project root."
        )
    return value


DATABASE_URL = _require_env("DATABASE_URL")

# Minutes a session stays valid from login, without renewal (see
# spec/control/core.md, Authentication section).
CONTROL_SESSION_TTL_MINUTES = int(os.environ.get("CONTROL_SESSION_TTL_MINUTES", "15"))

"""Carga de configuración compartida por los scripts de importación.

Lee el .env de la raíz del proyecto (mismo fichero que usa db/, ver
spec/db/general.md), de forma independiente al resto de la app.
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
            f"{name} no está definida. Añádela al fichero .env en la raíz del proyecto."
        )
    return value


AEMET_API_KEY = _require_env("AEMET_API_KEY")
DATABASE_URL = _require_env("DATABASE_URL")

"""Carga de configuración de control/backend/.

Reutiliza el .env de la raíz del proyecto (mismo fichero que usan db/
e importa/, ver spec/db/general.md), de forma independiente al resto
de la app (entorno virtual propio, ver spec/control/core.md).
"""

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / ".env")


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(
            f"{name} no está definida. Añádela al fichero .env en la raíz del proyecto."
        )
    return value


DATABASE_URL = _require_env("DATABASE_URL")

# Minutos de validez de una sesión desde el login, sin renovación
# (ver spec/control/core.md, sección Autenticación).
CONTROL_SESSION_TTL_MINUTOS = int(os.environ.get("CONTROL_SESSION_TTL_MINUTOS", "15"))

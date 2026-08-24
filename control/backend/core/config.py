"""Carga de configuración de control/backend/.

Reutiliza el .env de la raíz del proyecto (mismo fichero que usan db/
e importa/, ver spec/db/general.md), de forma independiente al resto
de la app (entorno virtual propio, ver spec/control/core.md).
"""

import os
from pathlib import Path

from dotenv import load_dotenv

try:
    # En desarrollo local (venv), config.py vive en
    # control/backend/core/ dentro del repo completo, así que subir 3
    # niveles llega a la raíz del proyecto donde está el .env.
    PROJECT_ROOT = Path(__file__).resolve().parents[3]
    load_dotenv(PROJECT_ROOT / ".env")
except IndexError:
    # En el contenedor Docker solo se copia control/backend/ (ver
    # Dockerfile), así que esa profundidad de directorios no existe.
    # No pasa nada: docker-compose.yml ya inyecta las variables de
    # entorno directamente, no hace falta leer un .env.
    pass


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

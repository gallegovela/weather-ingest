#!/usr/bin/env python3
"""Script de actualización de la base de datos.

Punto de entrada único para tocar el esquema, en vez de invocar
`alembic` directamente (ver spec/db/general.md). Ejecuta siempre
alembic con cwd=db/ para que `script_location = migrations` en
alembic.ini se resuelva de forma correcta sin importar desde dónde
se lance este script.

Uso:
    python db/migrate.py upgrade
    python db/migrate.py downgrade
    python db/migrate.py current
    python db/migrate.py history
    python db/migrate.py new "create_estaciones"
"""

import subprocess
import sys
from pathlib import Path

DB_DIR = Path(__file__).resolve().parent

SIMPLE_COMMANDS = {
    "upgrade": ["upgrade", "head"],
    "downgrade": ["downgrade", "-1"],
    "current": ["current"],
    "history": ["history"],
}


def build_args(argv: list[str]) -> list[str] | None:
    if not argv:
        return None

    command, rest = argv[0], argv[1:]

    if command == "new":
        if not rest:
            return None
        return ["revision", "-m", rest[0]]

    if command in SIMPLE_COMMANDS and not rest:
        return SIMPLE_COMMANDS[command]

    return None


def main() -> int:
    args = build_args(sys.argv[1:])
    if args is None:
        print(__doc__, file=sys.stderr)
        return 1

    result = subprocess.run(["alembic", "-c", "alembic.ini", *args], cwd=DB_DIR)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())

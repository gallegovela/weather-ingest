#!/usr/bin/env python3
"""Database update script.

Single entry point for touching the schema, instead of invoking
`alembic` directly (see spec/db/general.md). Always runs alembic with
cwd=db/ so that `script_location = migrations` in alembic.ini resolves
correctly regardless of where this script is launched from.

Usage:
    python db/migrate.py upgrade
    python db/migrate.py downgrade
    python db/migrate.py current
    python db/migrate.py history
    python db/migrate.py new "create_stations"
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

# Database build (PostgreSQL + Alembic)

This document describes how the project's database schema is built
and versioned. It complements
[`spec/db/tables.md`](./tables.md), where each table's design is
documented: this document covers the **mechanism** (tooling, paths,
conventions and workflow), not the content of the tables.

## Database engine

- **Engine:** PostgreSQL.
- **Migration tool:** [Alembic](https://alembic.sqlalchemy.org/),
  used in **plain SQL** mode (migrations hand-written with
  `op.execute(...)` / `alembic.op` helpers), **without** needing to
  define SQLAlchemy ORM models. Alembic is used purely as the
  versioning and migration-application engine.

## Independence from the rest of the application

The database build is a **self-contained** module, independent of
the ingestion code (import scripts). It lives in its own folder at
the project root and shares no code, import dependencies, or
lifecycle with the rest of the app: the database can be
created/migrated without running or importing anything else from the
project, and vice versa.

## Directory structure

All paths are relative to the project root (`/var/www/weather`):

```
db/                             # Independent database build module
├── alembic.ini                 # Alembic configuration (reads DATABASE_URL from the environment)
├── requirements.txt            # Dependencies specific to this module (alembic, psycopg, python-dotenv)
├── migrate.py                  # Update script (entry-point wrapper, see below)
└── migrations/
    ├── env.py                  # Alembic entry point: DB connection and migration context
    ├── script.py.mako          # Template used when generating new migrations
    └── versions/                # One table/change documented in spec/db/tables.md = one migration
        ├── 20260822_1030_a1b2c3_create_stations.py
        └── ...
```

- `db/` is a sibling of `spec/`, `.env`, `CLAUDE.md`, etc. at the
  project root — it doesn't hang off any future application `src/`.
- `db/requirements.txt` is kept separate from the ingestion app's
  `requirements.txt`, precisely so this module can be installed and
  run in isolation (e.g. in a separate deployment step).

## Environment variables

The same project-root `.env` is reused (not versioned). New
variables needed by this module:

| Variable       | Description                                              | Example                                              |
|----------------|-----------------------------------------------------------|-------------------------------------------------------|
| `DATABASE_URL` | PostgreSQL connection string used by Alembic and by the app | `postgresql+psycopg://weather:******@localhost:5432/weather` |

**Note on the URL scheme:** `postgresql+psycopg://` is used (not
plain `postgresql://`). SQLAlchemy picks `psycopg2` by default for
the generic `postgresql://` scheme, and this project uses `psycopg`
v3 (see below), which isn't installed — the `+psycopg` dialect suffix
must be explicit.

`db/alembic.ini` doesn't contain the connection string in plain text:
`env.py` reads it from `DATABASE_URL` (loading `.env` with
`python-dotenv`) and passes it to Alembic at runtime.

## Naming conventions

### Tables

- Lowercase, in English, `snake_case`, **plural** (e.g. `stations`,
  `climatological_values`).
- Table name = business concept, no technical prefixes (no `tbl_`,
  `t_`, etc.).

### Columns

- Lowercase, in English, `snake_case`.
- **Natural primary key**: when the data source already provides a
  stable, unique identifier (e.g. AEMET's `station_code` in
  `stations`), that column is used as the primary key instead of
  creating an artificial `id`.
- **Technical primary key**: if there's no clear natural key, use
  `id BIGINT GENERATED ALWAYS AS IDENTITY` (or `BIGSERIAL`).
- **Foreign keys**: `<singular_table>_<referenced_column>` (e.g. a
  future table referencing `stations` would use `station_code`).
- **Audit columns** (mandatory on every table fed by an ingestion
  process): `created_at` (timestamp of first insert) and
  `updated_at` (timestamp of the last sync), as defined in
  `spec/db/tables.md`.

### Indexes and constraints

- Index name: `ix_<table>_<column(s)>`.
- Unique constraint name: `uq_<table>_<column(s)>`.
- Foreign key name: `fk_<source_table>_<target_table>`.

### Migration files

- Generated with `alembic revision -m "create_stations"` (or the
  `migrate.py new "create_stations"` wrapper, see below).
- File name template (configured in `alembic.ini` via
  `file_template`):
  `%%(year)d%%(month).2d%%(day).2d_%%(hour).2d%%(minute).2d_%%(rev)s_%%(slug)s`
  → example: `20260822_1030_a1b2c3_create_stations.py`.
- This gives file names that sort chronologically in a directory
  listing, plus the revision hash (`rev`) that Alembic needs
  internally for migration chaining.
- **One migration = one schema change with its own identity**:
  creating a table, adding a column, creating an index... Unrelated
  changes are not grouped into the same migration.

## Update script (`db/migrate.py`)

Command-line wrapper, meant to avoid having to remember the full
`alembic` syntax and its configuration flags:

| Command                          | Equivalent to                          | Use                                                  |
|-----------------------------------|--------------------------------------|-------------------------------------------------------|
| `python db/migrate.py upgrade`    | `alembic -c db/alembic.ini upgrade head` | Applies all pending migrations.                  |
| `python db/migrate.py downgrade`  | `alembic -c db/alembic.ini downgrade -1` | Reverts the last applied migration.              |
| `python db/migrate.py new "<message>"` | `alembic -c db/alembic.ini revision -m "<message>"` | Creates a new empty migration file in `versions/`. |
| `python db/migrate.py current`    | `alembic -c db/alembic.ini current`  | Shows the last migration applied to the current DB. |
| `python db/migrate.py history`    | `alembic -c db/alembic.ini history`  | Lists the full migration history.                    |

This script is the only recommended entry point for touching the
schema; it avoids running `alembic` directly so the `-c
db/alembic.ini` flag isn't forgotten (the configuration file isn't
at the project root, but inside `db/`).

## Workflow to add/change a table

1. Document (or update) the table in `spec/db/tables.md` first:
   columns, types, keys, design notes.
2. Generate the migration: `python db/migrate.py new "create_<table>"`.
3. Write the `upgrade()` (creation/alteration DDL) and the
   `downgrade()` (inverse DDL) in the generated file, using plain SQL
   (`op.execute(...)`) or `alembic.op` helpers (`op.create_table`,
   `op.add_column`, etc.) — both are valid, clarity is prioritized.
4. Apply the migration locally: `python db/migrate.py upgrade`.
5. Verify with `python db/migrate.py current`.

## Incremental build

The full database schema is never defined all at once: it's built
**exclusively** through the ordered sequence of migrations in
`db/migrations/versions/`. Bringing up a brand-new database always
consists of the same command (`python db/migrate.py upgrade`), which
reproduces the schema by applying all migrations in order. No tables
are created nor schema changes applied by hand or by any other means.

## Implementation status

The `db/` module is already implemented following this
specification: `db/alembic.ini`, `db/migrate.py`,
`db/migrations/env.py`, `db/migrations/script.py.mako` and
`db/migrations/versions/`. Dependencies installed in the project's
own virtual environment (`.venv/`, not versioned) from
`db/requirements.txt`.

**Connection driver chosen:** `psycopg` v3 (`psycopg[binary]`
package), as it's the actively maintained driver recommended by
SQLAlchemy for PostgreSQL (`psycopg2` is in maintenance mode).

The first real migration, `create_stations`, already exists and
creates the `stations` table (see `spec/db/tables.md`). The
development PostgreSQL server is started with `docker-compose.yml`
(project root), with credentials matching `DATABASE_URL` in `.env`.
There's no production server yet.

## Environments, permissions and backups — decided

- **Environment management:** a single active `DATABASE_URL` via
  `.env`, with no support for multiple environments within the same
  `alembic.ini`. Local today, production once a server exists; if a
  test database is ever needed, it's solved with an explicitly loaded
  `.env.test`, without "environment" being a concept Alembic needs to
  know about.
- **PostgreSQL user and permissions:** a single user shared between
  migrations and the application (the same one `docker-compose.yml`
  already uses, `weather`/`weather` locally). No separate DDL-privileged
  user is split from a runtime read/write-only one: that separation
  isn't justified without several developers operating on the
  database or an explicit least-privilege requirement.
- **Backups:** no backup/restore strategy is implemented for now. The
  project's data is recoverable (re-importable from the AEMET API),
  so that extra complexity isn't justified at this point.
- **Production PostgreSQL server:** same pattern as locally — one
  more `postgres` container added to the target server's
  `docker-compose.yml`, consistent with the decision to containerize
  `control/backend/` and `control/frontend/` (see
  [`spec/control/core.md`](../control/core.md)), not an externally
  managed service (RDS, Cloud SQL, etc.).

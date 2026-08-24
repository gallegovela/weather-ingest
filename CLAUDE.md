# weather

## Language policy

**The whole project is written in English**: code (modules, functions,
variables), file/folder names, the database schema (tables, columns,
indexes, constraints), API routes/query params, environment variable
names, and all documentation (`CLAUDE.md`, `spec/`, READMEs, code
comments). The only exception is **domain data** — real-world Spanish
place names (provinces, station names) coming from AEMET — which is
data, not code, and stays as-is. User-facing text in the control
panel UI (labels, buttons, messages) is currently in Spanish and is
**not** part of this policy; it may be addressed separately later.

## Project specification

The full specification of the project (import scripts, database
tables, and whatever gets added later) is documented in the `.md`
files under the different sections of the `spec/` folder (e.g.
`spec/ingest/`, `spec/db/`).

**Before working on any part of the project you must review this
documentation in full** to have a complete, up-to-date picture of the
project, not just the section that looks relevant at first glance.

## Project summary

Python app that ingests weather data from an external API
(ingestion script/job). The objective, detailed scope, and
destination of the data will keep being defined in this document as
we move forward.

- **App type:** ingestion script/job (not a web service for now)
- **Language:** Python
- **Source API:** TBD — pending choice (e.g. OpenWeatherMap, AEMET,
  Open-Meteo, etc.)
- **Data destination:** TBD — file, database, another system?
- **Ingestion frequency:** TBD — on demand, cron, scheduler?

## Project structure

```
db/                  # Self-contained database build module (Alembic).
                     # See spec/db/general.md.
ingest/              # Ingestion scripts (one per source resource).
├── requirements.txt # Dependencies specific to the ingest module.
├── config.py        # .env loading (DATABASE_URL; AEMET_API_KEY lives in config_values, see spec/db/tables.md).
├── aemet_client.py  # Generic client for AEMET's two-step pattern (+429 retry/backoff).
├── db.py            # psycopg connection (plain SQL, no ORM) + config_values reads.
├── stations.py       # Job: station inventory (spec/ingest/STATIONS.md).
├── daily_values.py    # Job: daily climatological values (spec/ingest/DAILY_VALUES.md).
├── worker.py          # Job queue worker, drains ingest_jobs (spec/ingest/general.md).
├── Dockerfile          # ingest-worker image (build context: project root, see Dockerfile).
└── tests/              # pytest, see spec/testing.md.
control/             # Control panel (SPA + API). See spec/control/.
├── backend/          # FastAPI API (service + DAO layers), own virtual
│                     # environment and requirements.txt, independent
│                     # of the rest of the project.
│   ├── main.py        # FastAPI startup, mounts each module's router.
│   ├── core/           # Cross-cutting: config (.env), Postgres
│                       # connection, session validation (core/auth.py).
│   └── modules/         # A module = a folder (security, stations, ...),
│                       # each with router.py/service.py/dao.py/schemas.py.
└── frontend/         # React SPA (Vite), own node_modules, independent.
    ├── vite.config.js  # /api proxy to control/backend in development.
    └── src/
        ├── app/         # Cross-cutting: Layout (side menu), Login,
        │                # RequireAuth (session guard), apiClient.
        └── modules/      # A module = a folder (security, stations, ...),
                          # with its own screens and its <module>Api.js.
spec/                # Project specification (see above).
docker-compose.yml   # Local development PostgreSQL.
.env                 # Environment variables (not versioned).
```

Each future ingestion job (daily climatological values, etc.) adds
its own module inside `ingest/`, reusing `aemet_client.py` and
`db.py`. Each future control panel module adds its own folder inside
`control/backend/modules/` and `control/frontend/src/modules/`,
following the pattern set by the `stations` module (see
`spec/control/core.md`).

## Setup / environment

- **Dependency manager:** `pip` + `venv` (a single `.venv/` at the
  project root for `db/`/`ingest/`, not versioned).
  `control/backend/` has its own independent `.venv/` (see
  `spec/control/core.md`), also not versioned. `control/frontend/`
  uses `npm` with its own `node_modules/` (not versioned).
- **Environment variables** (`.env` file at the project root, not
  versioned, shared by `db/`, `ingest/` and `control/backend/`):
  - `DATABASE_URL` — PostgreSQL connection string, SQLAlchemy format
    with the `psycopg` v3 driver explicit:
    `postgresql+psycopg://user:password@host:5432/db`.
  - `CONTROL_SESSION_TTL_MINUTES` — minutes a control panel session
    stays valid from login, without renewal (defaults to `15` if not
    set — see `spec/control/core.md`).
  - `AEMET_API_KEY` is **not** read from here: it lives in the
    `config_values` database table (see `spec/db/tables.md`), read by
    `ingest/` at runtime. Not yet removed from `.env` (kept during the
    migration to `config_values`), but no code reads it from there
    anymore.
- **Local database:** `docker-compose.yml` starts a development
  PostgreSQL with the credentials already in `.env`
  (`weather`/`weather`/`weather`). Start it with `docker compose up -d`.
- **Installing dependencies:**
  ```
  source .venv/bin/activate
  pip install -r db/requirements.txt
  pip install -r ingest/requirements.txt
  ```
  For `control/backend/` (own virtual environment):
  ```
  cd control/backend
  python -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  ```
  For `control/frontend/`:
  ```
  cd control/frontend
  npm install
  ```

## Common commands

- `docker compose up -d` — start the local PostgreSQL.
- `python db/migrate.py upgrade` — apply pending migrations (see
  `spec/db/general.md` for the rest of `migrate.py` commands).
- `python -m ingest.stations` — import/update the AEMET
  climatological station inventory.
- `python -m ingest.daily_values --station <code> --from <date> --to <date>` —
  manually run a daily values import (normally queued from the panel
  instead, see `spec/control/module/jobs.md`).
- `python -m ingest.worker` — run the job queue worker locally
  (normally runs in the `ingest-worker` container, see
  `spec/ingest/general.md`).
- `pytest ingest/tests/` — run `ingest/`'s unit tests (see
  `spec/testing.md`).
- `cd control/backend && uvicorn main:app --reload` — start the
  control panel API in development (with `control/backend/`'s own
  `.venv` activated).
- `cd control/frontend && npm run dev` — start the control panel SPA
  in development (needs the backend running in parallel, see
  `control/frontend/README.md`). Alternative without local node:
  `docker compose --profile dev up control-frontend-dev`.
- `docker compose build control-frontend` — build the frontend
  production image (Vite build + nginx) without needing node locally.

## Code conventions

- English for everything: table/column names, `spec/` documentation,
  and Python code (modules, functions, variables) — see "Language
  policy" above. Real-world Spanish domain data (station names,
  provinces) is left as-is since it's data, not code.
- Each ingestion script is responsible for its own transform and load
  (upsert); there's no ORM or models shared with `db/` (which only
  manages the schema via migrations, see `spec/db/general.md`).
- Plain SQL with named parameters (psycopg's `%(key)s`), no query
  builders.

## Implementation order

When building a new piece of functionality that spans several parts
of the project (e.g. a new ingestion job with its own control panel
module), the fixed order is always: **`db/` → `ingest/` →
`control/backend/` → `control/frontend/`**. Schema first (the tables
the feature needs), then the ingestion/business logic that reads and
writes them, then the API that exposes that logic, then the UI that
consumes the API — never the other way around, so each layer only
ever gets built against a lower layer that already exists.

## Notes on the external API

- **AEMET OpenData**, authenticated via the `api_key` header, value
  read from the `config_values` table's `AEMET_API_KEY` key (see
  `spec/db/tables.md`), not from `.env`.
- Two-step pattern (initial request → temporary `datos` URL → actual
  content) and `ISO-8859-15` encoding in the data response: see
  `spec/ingest/STATIONS.md` for the detail, encapsulated in
  `ingest/aemet_client.py`.

## Decisions and additional context

- **Local PostgreSQL via Docker Compose** (`docker-compose.yml`,
  project root): there's no production server yet, so the
  development environment is started with a container whose
  credentials match `DATABASE_URL` in `.env`.
- **`DATABASE_URL` uses the `postgresql+psycopg://` scheme** (not
  plain `postgresql://`): SQLAlchemy/Alembic need the dialect suffix
  to pick the `psycopg` v3 driver instead of `psycopg2` (which isn't
  installed).
- **First migration created**: `create_stations`
  (`db/migrations/versions/20260822_2051_f54155bc39b7_create_stations.py`),
  with `latitude_decimal`/`longitude_decimal` as `NUMERIC(9,6)`
  (enough precision for coordinates in decimal degrees).
- **Ingestion without ORM or SQLAlchemy**: `ingest/` uses `psycopg` v3
  directly with plain SQL (`INSERT ... ON CONFLICT`), independent of
  `db/` (which only manages the schema).
- **HTTP library:** `requests`, for simplicity (synchronous script, no
  need for concurrency).

# weather-ingest

A Python data ingestion pipeline for weather data from
[AEMET OpenData](https://opendata.aemet.es/) (Spain's national
meteorological agency), backed by PostgreSQL and operated through a
web-based control panel.

## What this is

- **`ingest/`** — ingestion scripts that pull data from AEMET
  OpenData and load it into PostgreSQL. Currently imports the
  catalogue of climatological stations; more resources (e.g. daily
  climatological values) will be added as their own jobs, reusing the
  same AEMET client and DB helpers.
- **`db/`** — a self-contained schema module (Alembic migrations) for
  the PostgreSQL database, independent of the ingestion code.
- **`control/`** — a web control panel (FastAPI backend + React SPA
  frontend) for operating and monitoring the system without touching
  the command line or the database directly: login, station listing
  and map, user management, with more modules planned.

Each part is documented in detail under [`spec/`](spec/) — that's the
source of truth for design decisions, data flow, and API/database
specifics.

## Project layout

```
db/                  # Database schema module (Alembic migrations). See spec/db/.
ingest/              # Ingestion scripts (one per data source/resource).
control/             # Control panel (SPA + API). See spec/control/.
├── backend/          # FastAPI API (service + DAO layers).
└── frontend/         # React SPA (Vite).
spec/                # Full project specification.
docker-compose.yml   # Local PostgreSQL + control panel containers.
```

## Getting started

Requirements: Python 3, Node.js (or Docker, see below), Docker
Compose, and an [AEMET OpenData API
key](https://opendata.aemet.es/centrodedescargas/altaUsuario).

1. Create a `.env` file at the project root with your database
   connection string (see `CLAUDE.md` for the full list of expected
   variables: `DATABASE_URL`, etc.).
2. Start the local database:
   ```
   docker compose up -d
   ```
3. Apply database migrations:
   ```
   source .venv/bin/activate
   pip install -r db/requirements.txt -r ingest/requirements.txt
   python db/migrate.py upgrade
   ```
4. Set your [AEMET OpenData API
   key](https://opendata.aemet.es/centrodedescargas/altaUsuario): it's
   read from the `config_values` database table, not `.env` (see
   `spec/db/tables.md`). The migrations above seed a placeholder row;
   replace it with your real key:
   ```
   docker compose exec postgres psql -U weather -d weather -c \
     "UPDATE config_values SET value = 'your-real-key' WHERE key = 'AEMET_API_KEY'"
   ```
5. Run an ingestion job, e.g. the station inventory:
   ```
   python -m ingest.stations
   ```
6. (Optional) Run the control panel:
   ```
   cd control/backend && python -m venv .venv && source .venv/bin/activate \
     && pip install -r requirements.txt && uvicorn main:app --reload
   cd control/frontend && npm install && npm run dev
   ```
   or, without installing Node locally:
   ```
   docker compose --profile dev up control-frontend-dev
   ```

## Documentation

- [`CLAUDE.md`](CLAUDE.md) — project conventions, setup, and common
  commands.
- [`spec/`](spec/) — full specification: ingestion jobs, database
  schema, and control panel modules.

## Status

Early stage / work in progress. The station inventory ingestion job
and the control panel's authentication and stations modules are
implemented; further ingestion jobs (e.g. daily climatological
values) and control panel modules are planned.

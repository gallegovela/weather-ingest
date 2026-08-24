# Module: Jobs

Panel-visible label: **"Planificador"** (Spanish — see `CLAUDE.md`,
"Language policy": UI-facing text stays in Spanish; this file, like
the rest of the project's code and docs, is in English).

## Objective

Let an authenticated user queue ingestion runs for any of the
project's ingestion scripts — currently the station inventory import,
and, once implemented, the daily climatological values import by
station and date range — from the control panel, and follow their
status, without running scripts by hand or accessing the database
directly.

Jobs are queued **on demand, whenever the user wants**, with whatever
parameters they choose each time — **not** on a periodic/cron
schedule (decided; see
[`spec/ingest/general.md`](../../ingest/general.md) for how queued
jobs actually get executed).

## Menu

Top-level **"Planificador"** entry in the side menu (see "Application
structure" in `core.md`), with **one subitem per ingestion script**
(i.e. per `job_type`, see `spec/db/tables.md`, table `ingest_jobs`):

1. **Stations** — queue a station inventory import.
2. **Daily values** — queue a daily climatological values import for a
   station and date range.

**Unlike other modules**, where subitems are different views of the
same functional area (e.g. `stations` → List/Map over the same data),
here **each subitem is a self-contained screen tailored to that job
type's own parameters** — decided, since different ingestion scripts
need different inputs, from none (`stations`) to a station and a date
range (`daily_values`) to whatever a future script needs. This module
has no single reference screen the way `stations` is the reference for
paginated listings; each job-type screen follows the same small
pattern (parameter form if any + job history list), described per
screen below. Adding a new ingestion script means adding a new
subitem/screen here.

## Screens

### 1. Stations

- No parameters: a single **Queue import** button creates a new
  `ingest_jobs` row with `job_type = 'stations'` and empty `params`
  (`{}`).
- Below the button, a **history list** of past stations jobs (status,
  timestamps, row counts), most recent first, following the shared
  "Paginated listings with filters" convention (`core.md`): filterable
  by `status` and by `created_at` range.

### 2. Daily values

- Form with three fields, matching the parameters the underlying AEMET
  endpoint itself needs (see `spec/ingest/general.md` for how the job
  is executed; the ingestion script's own AEMET-specific detail is
  documented separately, when it's implemented):
  - **Station**: picker over the existing station catalog (`stations`
    table), searchable by code/name. Reuses the existing `GET
    /api/stations/stations` endpoint (see
    [`spec/control/module/stations.md`](./stations.md)) for the
    lookup — no new backend endpoint needed just for this picker.
  - **Date from** / **Date to**: the import's date range.
- **Queue import** button creates an `ingest_jobs` row with `job_type
  = 'daily_values'` and `params = {"station_code": ..., "date_from":
  ..., "date_to": ...}`.
- **Validation — decided:** both dates are required and `date_from <=
  date_to`, checked in the service layer before queuing (no DB
  `CHECK`, same criteria as the rest of the project). Whether there's
  a maximum allowed range doesn't need to be enforced at queueing time
  — AEMET's own per-request limit is handled by the worker chunking
  internally (`spec/ingest/general.md`), transparently to the user.
- Same **history list** pattern as the Stations screen, filtered to
  `job_type = 'daily_values'`, plus a filter by `station_code`.

## Data

Follows the layered architecture in `core.md`:

- **DAO** (`control/backend/modules/jobs/dao.py`): plain SQL against
  `ingest_jobs` (`spec/db/tables.md`) — insert a new job, list jobs
  filtered by `job_type` with pagination/filters.
- **Service** (`service.py`): validates `params` per `job_type` before
  inserting (e.g. `daily_values`'s date range as above); no other
  business logic.
- **Control** (`router.py`): exposes the endpoints.

### Endpoints (REST API)

One create + one list endpoint pair **per job type** — decided,
instead of a single generic `/api/jobs` endpoint taking `job_type` as
a parameter, so each screen's request/response contract stays specific
and typed (matches "each subitem is a self-contained screen" above).
The DAO/service still work against the single `ingest_jobs` table
internally.

- `POST /api/jobs/stations` — queue a stations import job (no body).
- `GET /api/jobs/stations` — paginated history of stations jobs,
  filterable by `status` and `created_at` range.
- `POST /api/jobs/daily-values` — queue a daily values import job.
  Body: `{"station_code", "date_from", "date_to"}`.
- `GET /api/jobs/daily-values` — paginated history of daily values
  jobs, filterable by `status`, `created_at` range and `station_code`.

## Pending decisions

- Whether/how to let a user cancel a `pending` job before the worker
  picks it up — not needed for a first version; revisit if the queue
  grows large enough for it to matter.
- Full parameter/behavior spec of the `daily_values` ingestion script
  itself (AEMET endpoint, chunking, rate limiting) — out of scope of
  this module, will live in its own `spec/ingest/` document when that
  script is implemented.

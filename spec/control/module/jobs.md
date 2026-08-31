# Module: Jobs

Panel-visible label: **"Planificador"** (Spanish — see `CLAUDE.md`,
"Language policy": UI-facing text stays in Spanish; this file, like
the rest of the project's code and docs, is in English).

## Objective

Let an authenticated user queue ingestion runs for any of the
project's ingestion scripts — the station inventory import, the daily
climatological values import by station and date range, and the daily
climatological values import for all stations at once — from the
control panel, and follow their status, without running scripts by
hand or accessing the database directly.

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
3. **Daily values (all stations)** — queue a daily climatological
   values import for every station at once, over a date range (see
   `spec/ingest/DAILY_VALUES.md`, "Import mode: all stations at once").

**Unlike other modules**, where subitems are different views of the
same functional area (e.g. `stations` → List/Map over the same data),
here **each subitem is a self-contained screen tailored to that job
type's own parameters** — decided, since different ingestion scripts
need different inputs, from none (`stations`) to a station and a date
range (`daily_values`) to a date range alone
(`daily_values_all_stations`) to whatever a future script needs. This
module has no single reference screen the way `stations` is the
reference for paginated listings; each job-type screen follows the same small
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
- Each row whose `status` is `pending` has a **Cancel** action (see
  "Cancelling a job" below); rows in any other status don't.
- Each row has a selection checkbox, plus a **Delete selected** action
  (see "Deleting jobs" below) enabled whenever at least one row is
  selected.

### 2. Daily values

- Form with three fields, matching the parameters the underlying AEMET
  endpoint itself needs (see
  [`spec/ingest/DAILY_VALUES.md`](../../ingest/DAILY_VALUES.md) for
  the ingestion script's own detail: AEMET endpoint, rate limiting):
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
  `CHECK`, same criteria as the rest of the project).
- **Maximum range per job — decided: `SCHEDULER_MAX_DATE_RANGE`.** A
  single `daily_values` job can't span more than
  `SCHEDULER_MAX_DATE_RANGE` days (`config_values`, seeded at `180` —
  see `spec/db/tables.md`); the service layer rejects (`400`) a create
  request that exceeds it. Because of this, by the time a job reaches
  the worker its range is already guaranteed to fit AEMET's own
  per-request limit in a single call — the ingestion script doesn't
  need to chunk it further (see `spec/ingest/DAILY_VALUES.md`).
- **Splitting a too-large range — decided:** if the user picks a range
  longer than `SCHEDULER_MAX_DATE_RANGE`, the screen **warns before
  queuing anything** (reading the current limit via the Config
  module's `GET /api/config/values`, see
  [`spec/control/module/config.md`](./config.md)) and offers two
  choices, instead of just failing on submit:
  - **Split into N imports**: the screen computes consecutive
    sub-ranges of at most `SCHEDULER_MAX_DATE_RANGE` days each covering
    the full selected period, and calls `POST /api/jobs/daily-values`
    once per sub-range — each becomes its own row in `ingest_jobs`,
    visible individually in the history list below.
  - **Redefine the range**: closes the warning without queuing
    anything, so the user can edit the dates.
- **Overlap warning — decided.** Before queuing (checked first, ahead
  of the range-length check above), the screen asks
  [`climatological_values`](./climatological_values.md)'s own listing
  endpoint how many days in `[date_from, date_to]` already have a
  value imported for that station (`GET
  /api/climatological-values/values?station_code=...&date_from=...
  &date_to=...&page_size=1`, reading `total` — no new backend endpoint,
  same "reuse an existing listing for a pre-flight check" pattern
  already used for the station picker). If `total > 0`, a confirmation
  dialog states how many days overlap and that they'll be
  **overwritten with the new import**, not duplicated (the upsert
  guarantees that — see `spec/ingest/DAILY_VALUES.md`, "Load
  strategy") — **Continue** proceeds to the range-length check and
  queuing as normal, **Cancel** returns to the form without queuing
  anything. Purely informational, not a hard block: overlapping is a
  legitimate, safe way to refresh a range (e.g. to pick up an AEMET
  correction), so nothing here prevents it — it only makes sure the
  user isn't surprised that it happened.
- Same **history list** pattern as the Stations screen, filtered to
  `job_type = 'daily_values'`, plus a filter by `station_code`, the
  same per-row **Cancel** action on `pending` jobs (see "Cancelling a
  job" below), and the same selection + **Delete selected** action
  (see "Deleting jobs" below).

### 3. Daily values (all stations)

- Form with **only** the two date fields — **no station picker**:
  unlike the Daily values screen, this job type has no `station_code`
  parameter (see `spec/ingest/DAILY_VALUES.md`, "Import mode: all
  stations at once").
  - **Date from** / **Date to**: the import's date range.
- **Queue import** button creates an `ingest_jobs` row with `job_type
  = 'daily_values_all_stations'` and `params = {"date_from": ...,
  "date_to": ...}`.
- **Validation — decided:** same as the Daily values screen — both
  dates required, `date_from <= date_to`, checked in the service layer.
- **Maximum range per job — pending, tied to the same open question in
  `spec/ingest/DAILY_VALUES.md`.** Whether this screen enforces
  `SCHEDULER_MAX_DATE_RANGE` (same key as Daily values) or a dedicated,
  presumably shorter, limit (`SCHEDULER_MAX_DATE_RANGE_ALL_STATIONS`,
  see `spec/db/tables.md`, `config_values`, "Pending decisions")
  depends on the real AEMET range limit for the `todasestaciones`
  endpoint, still pending empirical verification. **Not implemented
  until that's resolved.**
- **Splitting a too-large range**: same "Split into N imports" /
  "Redefine the range" choice as the Daily values screen, once the
  applicable limit above is decided.
- **Overlap warning — decided: not applicable.** Unlike the Daily
  values screen, there's no single `station_code` to check
  `climatological_values` against before queuing — this job type
  always covers every station in the response, so a pre-flight overlap
  check would mean scanning the whole table rather than one station's
  rows. Overwriting on re-import is still the expected, accepted
  behavior (`spec/ingest/DAILY_VALUES.md`, "Load strategy"); this
  screen just doesn't warn about it first.
- Same **history list** pattern as the other two screens, filtered to
  `job_type = 'daily_values_all_stations'` (no `station_code` filter,
  since this job type doesn't have one), the same per-row **Cancel**
  action on `pending` jobs (see "Cancelling a job" below), and the same
  selection + **Delete selected** action (see "Deleting jobs" below).

## Cancelling a job

- **Decided: a `pending` job can be cancelled; a `running` one can't.**
  Once the worker has claimed a job there's no way to interrupt it
  mid-run (see `spec/ingest/general.md`) — cancelling only ever
  prevents a job that hasn't started yet from starting.
- Implemented as a conditional update (`spec/db/tables.md`,
  `ingest_jobs` design notes) so there's no race against the worker
  claiming the same job at the same time: if the job is no longer
  `pending` by the time the cancel request runs, it fails with `400`
  instead of cancelling a job that's already executing.
- No confirmation dialog needed (unlike deleting a security user):
  cancelling a queued-but-not-started job isn't destructive to any
  data already written.

## Deleting jobs

- **Decided: no automatic retention policy — manual deletion from the
  history list instead** (see `spec/db/tables.md`, `ingest_jobs`,
  "Pending decisions"). Every row has a selection checkbox; a
  **Delete selected** button above the list removes every checked row.
- **One action for one or many — decided:** there's no separate
  "delete this row" vs. "delete these rows" — selecting a single row
  and using the same **Delete selected** action covers the single-row
  case too, instead of duplicating the action per row.
- **No status restriction — decided:** any row can be deleted
  regardless of `status`, including `pending` or `running` ones (see
  `spec/db/tables.md` for what that means for a `running` job). Unlike
  cancelling, this isn't about stopping a job — it's cleaning up
  history.
- **Confirmation dialog required** (same pattern as deleting a
  security user, `spec/control/module/security.md`): deleting is
  irreversible, so the panel confirms before calling the delete
  endpoint, stating how many jobs will be removed.

## Data

Follows the layered architecture in `core.md`:

- **DAO** (`control/backend/modules/jobs/dao.py`): plain SQL against
  `ingest_jobs` (`spec/db/tables.md`) — insert a new job, list jobs
  filtered by `job_type` with pagination/filters, the conditional
  `UPDATE ... WHERE status = 'pending'` used to cancel one, and
  `DELETE ... WHERE id = ANY(%(ids)s) AND job_type = %(job_type)s` for
  bulk delete (the `job_type` filter keeps the Stations screen from
  ever deleting a Daily values row or vice versa, even though both
  live in the same table).
- **Service** (`service.py`): validates `params` per `job_type` before
  inserting (e.g. `daily_values`'s date range and
  `SCHEDULER_MAX_DATE_RANGE` as above); on cancel, raises `400` if the
  DAO's conditional update affected zero rows; delete has no
  validation beyond the `ids` list being non-empty.
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
- `POST /api/jobs/stations/{id}/cancel` — cancel a `pending` stations
  job (see "Cancelling a job" above). `400` if it's not `pending`
  anymore.
- `POST /api/jobs/daily-values` — queue a daily values import job.
  Body: `{"station_code", "date_from", "date_to"}`.
- `GET /api/jobs/daily-values` — paginated history of daily values
  jobs, filterable by `status`, `created_at` range and `station_code`.
- `POST /api/jobs/daily-values/{id}/cancel` — cancel a `pending` daily
  values job. Same `400` behavior as above.
- `POST /api/jobs/daily-values-all-stations` — queue a daily values
  (all stations) import job. Body: `{"date_from", "date_to"}` — no
  `station_code`, unlike `POST /api/jobs/daily-values`.
- `GET /api/jobs/daily-values-all-stations` — paginated history of
  daily values (all stations) jobs, filterable by `status` and
  `created_at` range (no `station_code` filter — this job type has no
  such param).
- `POST /api/jobs/daily-values-all-stations/{id}/cancel` — cancel a
  `pending` daily values (all stations) job. Same `400` behavior as
  above.
- **`POST .../cancel`, not `DELETE`** — decided: the row isn't removed
  (a cancelled job is kept as history, `spec/db/tables.md`), only its
  `status` changes, so this is an action/state-transition endpoint
  rather than the "delete a resource" semantics `DELETE` implies in
  this project's REST contract (`core.md`).
- `DELETE /api/jobs/stations` — body `{"ids": [1, 2, 3]}`, deletes the
  given stations jobs. Works the same for a single id (`{"ids": [1]}`)
  — see "Deleting jobs" above, "one action for one or many".
- `DELETE /api/jobs/daily-values` — same, for daily values jobs.
- `DELETE /api/jobs/daily-values-all-stations` — same, for daily values
  (all stations) jobs.
- **`DELETE` with a body, scoped per job type** — decided: this one
  *is* a real deletion, so `DELETE` is the right verb (contrast with
  `.../cancel` above); a body carrying a list of ids is used instead
  of one call per id, matching "one action for one or many" in
  "Deleting jobs". Scoping each endpoint to its own job type (rather
  than one shared `DELETE /api/jobs`) follows the same "one
  create/list/cancel pair per job type" reasoning already used for the
  rest of this module's endpoints.

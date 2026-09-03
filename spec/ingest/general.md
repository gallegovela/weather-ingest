# Ingestion (general)

This document describes the mechanism shared by every ingestion job:
how a queued run gets executed. It complements each resource-specific
file (e.g. [`spec/ingest/STATIONS.md`](./STATIONS.md)), which documents
the **content** of a given ingestion job (data source, transformations,
load strategy) — this document covers the **execution mechanism**, not
what any particular job does with the data. Same split as
`spec/db/general.md` (mechanism) vs `spec/db/tables.md` (each table's
design).

## Job execution model — decided: DB-backed queue + single worker process

- Every ingestion run — whether queued from the "Stations" or "Daily
  values" screen of the control panel's Jobs module (see
  [`spec/control/module/jobs.md`](../control/module/jobs.md)), or from
  any future one — is represented as a row in the `ingest_jobs` table
  (see [`spec/db/tables.md`](../db/tables.md)), created by
  `control/backend/modules/jobs/`.
- A separate, long-running Python process (the **job worker**) polls
  that table and executes jobs one at a time: claim the oldest
  `pending` row (`FOR UPDATE SKIP LOCKED`, see `spec/db/tables.md`),
  mark it `running`, execute the corresponding ingestion logic, mark it
  `success` or `error` with the result.
- **Exactly one job per loop iteration — decided:** even if several
  jobs are `pending`, the worker claims and runs a single one, then
  sleeps for `POLL_INTERVAL_SECONDS` (see below) before checking again
  — it never drains the whole backlog in a burst. This bounds how much
  load the worker can put on AEMET (rate limits) and the database at
  once, regardless of how many jobs get queued from the panel.
- **Why a queue instead of running the ingestion synchronously inside
  the API request that creates the job:** a date-range import can take
  long enough (AEMET rate limits, large ranges) to time out an HTTP
  request. Queuing it lets the control panel respond immediately and
  the user follow progress by polling the job's status, instead of the
  request hanging until the import finishes.
- **Why a single polling worker instead of system cron or a scheduling
  library (APScheduler, Celery beat, etc.):** the requirement isn't
  "run this at a fixed time", it's "keep draining a queue the user
  fills whenever they want, with whatever parameters they want" — a
  scheduling tool solves a different problem (calendar/interval
  triggers), not this one. `FOR UPDATE SKIP LOCKED` keeps job claiming
  correct even if more than one worker process is ever run, though
  today there's exactly one.
- **Poll interval — configurable via `config_values`:** the worker
  reads the `POLL_INTERVAL_SECONDS` key (see `spec/db/tables.md`, table
  `config_values`; seeded at `300`, 5 minutes) at the start of each
  loop iteration, so the interval can be changed from the control
  panel's Config module (see
  [`spec/control/module/config.md`](../control/module/config.md))
  without redeploying.

## Job dispatch

- The worker maps each `ingest_jobs.job_type` to the ingestion function
  that handles it (`stations` → `ingest.stations.run_import`,
  `daily_values` → `ingest.daily_values.run_import`,
  `daily_values_all_stations` → `ingest.daily_values.run_import_all_stations`
  — see `spec/ingest/DAILY_VALUES.md`, "Import mode: all stations at
  once"), a function that takes the job's `params` (a `dict`, `{}` for
  `stations` since it takes none) and returns a result the worker turns
  into `rows_inserted`/`rows_updated` on the `ingest_jobs` row. Adding
  a new ingestion script means adding a new entry to this mapping — no
  schema change, since `params` is already a flexible `jsonb` column
  (see `spec/db/tables.md`).
- Each ingestion function keeps being responsible for its own
  transform/load, as today (`CLAUDE.md`, "Code conventions"); the
  worker's job is only to claim rows, invoke the right function, and
  record the outcome (`rows_inserted`, `rows_updated`, `error_message`)
  back on the `ingest_jobs` row. Any exception raised by an ingestion
  function is caught by the worker, stored in `error_message`, and
  marks the job `error` rather than crashing the worker loop.

## Deployment

- **Decided: containerized**, same criteria as the rest of the project
  (see `spec/control/core.md`, "Deployment"): a new `ingest-worker`
  service in `docker-compose.yml`, built from `ingest/` (its own
  `Dockerfile`, reusing `ingest/requirements.txt`), independent of
  `control/backend/` and `control/frontend/`.

## Pending decisions

- **Retry policy for `error` jobs**: none for now — consistent with
  `spec/ingest/STATIONS.md`'s existing "no retries" decision for the
  stations job. A failed job stays `error`; the user queues a new one
  if needed.
- **Graceful shutdown**: whether the worker needs to finish its
  current job before exiting on a stop signal — revisit once this runs
  somewhere less disposable than local development.
- **Concurrency**: whether more than one job should ever run at once
  (today: strictly one at a time, one worker process, one job claimed
  per loop iteration) — no known need for it yet.

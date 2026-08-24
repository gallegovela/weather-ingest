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
  reads the `poll_interval_seconds` key (see `spec/db/tables.md`,
  table `config_values`) at the start of each loop iteration, so the
  interval can be changed from the control panel's Config module (see
  [`spec/control/module/config.md`](../control/module/config.md))
  without redeploying.

## Job dispatch

- The worker maps each `ingest_jobs.job_type` to the ingestion function
  that handles it (e.g. `stations` → `ingest.stations`'s import logic,
  `daily_values` → the future `ingest.daily_values`'s import logic),
  passing the job's `params` as arguments. Adding a new ingestion
  script means adding a new entry to this mapping — no schema change,
  since `params` is already a flexible `jsonb` column (see
  `spec/db/tables.md`).
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

# Ingestion: Climatological metrics

## Objective

Ingestion script that computes metrics **derived from** the daily
climatological values already imported into `climatological_values`
(see [`spec/db/tables.md`](../db/tables.md)), for a given station and
date range. Unlike `ingest/stations.py` and `ingest/daily_values.py`,
this job's data source is **internal** (the project's own database),
not an AEMET endpoint — it doesn't use `ingest/aemet_client.py` at
all.

Three metrics are requested (see issue #6):

1. **Daily temperature range**: the difference between a day's
   maximum and minimum temperature.
2. **Day-over-day temperature differences**: the difference between a
   day's maximum (and, separately, minimum) temperature and the
   immediately previous day's.
3. **Total rainy days in the imported period**: how many days in the
   job's date range counted as having rain.

Like `daily_values`, this job always runs with **parameters** — a
station and a date range — supplied either by the job that triggers
it or queued automatically (see "Automatic triggering" below and
[`spec/control/module/jobs.md`](../control/module/jobs.md)).

## Data source and granularity

Metrics 1 and 2 are a fact **per station/day**, the same granularity
as `climatological_values` itself, so they're persisted one row per
station/day in the new `climatological_metrics` table (see
`spec/db/tables.md`). Metric 3 is an **aggregate over the job's whole
date range** (a count, not a per-day fact), so it isn't stored as a
table row at all — it's reported directly on the `metrics` job itself
(`ingest_jobs.result`, see "Load strategy" below), the same way
`rows_inserted`/`rows_updated` already report a run's outcome without
a dedicated table.

## Source fields (read, not written)

Read from `climatological_values` (see `spec/db/tables.md`) for every
day in `[date_from, date_to]` for the given `station_code`, plus the
single day immediately before `date_from` (needed for the first day's
day-over-day difference, see "Formulas" below):

- `max_temperature`, `min_temperature`: feed metrics 1 and 2.
- `precipitation_mm`, `precipitation_raw`: feed metric 3 (see "Rainy
  day definition" below).

## Formulas

1. **`temperature_range`** = `max_temperature - min_temperature` for
   that day. `NULL` if either is `NULL` (see `spec/db/tables.md`,
   `climatological_metrics`).
2. **`max_temperature_diff_prev_day`** = that day's `max_temperature`
   minus the immediately previous calendar day's `max_temperature`.
   **`min_temperature_diff_prev_day`**: same, for `min_temperature`.
   `NULL` when either day's value is missing — including when the
   previous day has **no** `climatological_values` row at all (e.g.
   the first day ever imported for a station, or a gap in the
   import). This is a `NULL` result, not a job failure (see "Job
   flow" below).
3. **Rainy days (period aggregate)**: count of days in
   `[date_from, date_to]` that qualify as a rainy day (see "Rainy day
   definition" below), out of the days that have a
   `climatological_values` row at all (a day with no row — a gap in
   the import — isn't counted either way, it's simply excluded from
   both the numerator and the denominator).

## Rainy day definition — decided

A day counts as rainy if `precipitation_mm > 0` **or**
`precipitation_raw = 'Ip'` (trace rain, <0.1mm — real rain fell even
though it couldn't be numerically measured, see `spec/db/tables.md`).
Days where `precipitation_raw = 'Acum'` are **excluded** from the
count (neither rainy nor not-rainy): that day's actual figure is
unknown, folded into a later accumulated reading, so there's no real
data to classify — same distinction `spec/db/tables.md` already makes
between `Ip`/`Acum`/`NULL`.

## Load strategy

- **Metrics 1 and 2**: **upsert** into `climatological_metrics` by
  (`station_code`, `date`) — same strategy as `climatological_values`
  (if the row already exists, e.g. re-running the job after the
  underlying values changed, it's overwritten; if not, it's
  inserted). Reported back as `rows_inserted`/`rows_updated` on the
  `ingest_jobs` row, same convention as every other job type.
- **Metric 3**: not upserted anywhere — written directly to the job's
  own `ingest_jobs.result` column as `{"rainy_days": N}` when the job
  finishes, so it's visible in the Jobs module's history without
  recomputing it (see `spec/control/module/jobs.md`).

## Job flow (summary)

Executed by the job worker (`spec/ingest/general.md`) for a `metrics`
job with `params = {station_code, date_from, date_to}`:

1. Read `climatological_values` for `station_code` over
   `[date_from - 1 day, date_to]` (the extra leading day covers
   `date_from`'s own day-over-day difference).
2. For each day in `[date_from, date_to]` that has a row, compute
   `temperature_range` and the two day-over-day differences (see
   "Formulas"), `NULL` where the needed source value is missing.
3. Upsert each computed row into `climatological_metrics`.
4. Count rainy days over the same range (see "Rainy day definition").
5. Report `rows_inserted`/`rows_updated` and
   `result = {"rainy_days": N}` back on the `ingest_jobs` row.

There's no call to AEMET, so there's no `estado`/`429`/network error
handling to do here — the only failure mode is an unexpected error
reading from or writing to the local database, which the worker
already catches generically (`spec/ingest/general.md`, "Job
dispatch").

## Automatic triggering

In addition to being queued manually like any other job type (see
`spec/control/module/jobs.md`), a `metrics` job is queued
**automatically** whenever a `daily_values` job finishes with
`success`, for the same `station_code`/`date_from`/`date_to` (see
`spec/ingest/general.md`, "Job dispatch") — so the metrics table stays
in sync with the values that fed it without an extra manual step.

## Implementation

Script in `ingest/metrics.py`, reusing `ingest/db.py` for the
database connection — no use of `ingest/aemet_client.py` (see
"Objective"). The actual logic lives in `run_import()`, invoked by
the job worker (`spec/ingest/general.md`), same pattern as
`ingest/daily_values.py`'s `run_import()`.

## Additional decisions

- **One job = one station — decided**, same criterion as
  `daily_values`: "several stations" (as requested in issue #6) is
  handled by queuing one job per station, not by a single job
  accepting a list — see `spec/control/module/jobs.md`.
- **No retries — decided.** There's no external API involved, so
  there's no transient failure mode (rate limiting, network) to retry
  — same "no retries" spirit as `spec/ingest/STATIONS.md`, for a
  different reason (nothing here is expected to fail transiently).
- **No change history — decided.** See `spec/db/tables.md`,
  `climatological_metrics`.

## Pending decisions

None.

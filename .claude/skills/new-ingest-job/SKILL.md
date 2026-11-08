---
name: new-ingest-job
description: Step-by-step guide to adding a new AEMET ingestion job to this project (destination table migration, ingest/<resource>.py module with transform/upsert, job worker registration, tests), following the patterns of ingest/stations.py and ingest/daily_values.py. Use when implementing a new ingestion script or a new job_type.
---

# Adding a new ingestion job

An ingestion job fetches one AEMET resource, transforms each record
and upserts it into its own table. Two jobs already exist and are the
reference implementations — read both before writing a new one:

- `ingest/stations.py` — no parameters, change history table.
- `ingest/daily_values.py` — parameters (station + date range),
  decimal-comma and sentinel parsing.

The job's own spec (`spec/ingest/<RESOURCE>.md`) is the source of
truth for the endpoint, field mapping, transformations and load
strategy; `spec/ingest/general.md` for how the worker runs it;
`spec/db/tables.md` for the destination table. Never invent a field
mapping or a design decision the spec doesn't state — raise it instead.

Follow `CLAUDE.md`'s implementation order: `db/` -> `ingest/` ->
`control/backend/` -> `control/frontend/`.

## 1. `db/` — destination table

```
.venv/bin/python db/migrate.py new "create_<table>"
```

- Write the migration with `op.execute(...)` plain SQL, like the
  existing ones in `db/migrations/versions/` (look at
  `*_create_climatological_values.py` for a table keyed by the
  upsert's conflict columns). Implement `downgrade()` too.
- The table's primary key (or a unique constraint) must match the
  upsert's `ON CONFLICT (...)` columns exactly — that's what makes
  re-imports idempotent.
- Include `created_at`/`updated_at` (`timestamp NOT NULL DEFAULT
  now()`, same type as the other ingested tables); the upsert sets
  `updated_at = now()` on update.
- Coordinates in decimal degrees use `NUMERIC(9,6)`.
- Never edit an already-applied migration: add a new one.

## 2. `ingest/<resource>.py` — the job module

Skeleton (mirror the existing modules' structure, naming and
docstrings):

```python
"""Import of <what> from AEMET.

See spec/ingest/<RESOURCE>.md for the detail of the process and
spec/db/tables.md for the destination schema.

Usage:
    python -m ingest.<resource> [--args]
"""

import logging
from dataclasses import dataclass

from ingest import aemet_client, db

ENDPOINT = "https://opendata.aemet.es/opendata/api/..."   # or ENDPOINT_TEMPLATE

UPSERT_SQL = """
    INSERT INTO <table> (<columns>) VALUES (%(col)s, ...)
    ON CONFLICT (<key columns>) DO UPDATE SET
        col = EXCLUDED.col,
        ...,
        updated_at = now()
    RETURNING (xmax = 0) AS inserted
"""

log = logging.getLogger("ingest.<resource>")


@dataclass
class ImportResult:
    received: int
    inserted: int
    updated: int
    errors: int


def transform(record: dict) -> dict:
    """Pure function: one raw AEMET record -> one row dict whose keys
    match UPSERT_SQL's named parameters."""


def run_import(params: dict | None = None) -> ImportResult:
    ...


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    ...


if __name__ == "__main__":
    main()
```

Rules the existing jobs follow — keep them:

- **Fetch only through `aemet_client.fetch(endpoint)`.** It handles
  the two-step `datos` pattern, the `api_key` header (read from
  `config_values`, never `.env`), ISO-8859-15 decoding and the `429`
  retry/backoff. Don't call `requests` directly.
- **Database only through `db.connect()`**, psycopg v3, plain SQL with
  named parameters (`%(key)s`). No ORM, no SQLAlchemy, no query
  builders, no string formatting of values into SQL.
- **`transform()` is pure** (no I/O) so it can be unit-tested:
  `.strip()` strings, parse AEMET's decimal comma
  (`float(raw.replace(",", "."))`), map absent optional fields to
  `None`, keep non-numeric sentinels in a `*_raw` column if the spec
  says so (see `daily_values.transform()`'s `prec` handling).
- **One commit per record, errors counted not raised**: inside the
  loop, `try: transform + execute + fetchone + commit` / `except
  Exception: rollback, errors += 1, log.exception(...)`. One bad
  record must not abort the whole import.
- **Count inserts vs. updates** with `RETURNING (xmax = 0) AS
  inserted`.
- **Log a summary** at the end (`received/inserted/updated/errors`)
  and return the `ImportResult`.
- **`run_import(params)` signature**: always accepts a `params` dict
  (`None`/`{}` if the job takes none) — the worker calls every job the
  same way. Validation of parameter ranges (e.g. max date range)
  belongs to the control panel when the job is created, not here.
- **CLI `main()`** for manual runs: `argparse` arguments mapped to the
  same `params` dict the worker would pass.
- Errors that should fail the whole job (bad envelope, rate limit
  exhausted) are raised (`aemet_client.AemetError`); the worker marks
  the job `error` with the message.

## 3. Register the job type in the worker

Add the entry to `JOB_HANDLERS` in `ingest/worker.py`:

```python
JOB_HANDLERS = {
    "stations": stations.run_import,
    "daily_values": daily_values.run_import,
    "<job_type>": <resource>.run_import,
}
```

`ingest_jobs.job_type` has no `CHECK` constraint and `params` is
`jsonb`, so no schema change is needed for a new job type. The
`ingest/Dockerfile` image picks up the new module without changes
(it copies `ingest/`); check it anyway if you add a dependency, which
goes in `ingest/requirements.txt`.

## 4. Tests

- **Unit tests** in `ingest/tests/test_<resource>.py` for `transform()`
  and any parsing helper: one test per rule (decimal comma, missing
  optional field -> `None`, each sentinel, dropped fields), using a
  `BASE_RECORD` dict like `ingest/tests/test_daily_values.py`. No
  network, no database.
- **Integration test** in `ingest/tests/integration/test_<resource>.py`
  only if the spec calls out a database-enforced guarantee (e.g.
  upsert idempotency, see `spec/testing.md`, "Known exceptions"):
  real connection, insert via `UPSERT_SQL`, assert, and roll back in
  the fixture so nothing is left behind.
- Run them with the `run-tests` skill.

## 5. Control panel (if the spec asks for it)

A new job type is usually queued from the control panel's Jobs module
(`spec/control/module/jobs.md`): a backend endpoint that validates the
parameters and inserts the `ingest_jobs` row
(`control/backend/modules/jobs/`), and a frontend screen
(`control/frontend/src/modules/jobs/`). Follow the existing
`stations`/`daily_values` job screens and endpoints, in that order
(backend first).

## 6. Docs

- Add the manual-run command to `CLAUDE.md`'s "Common commands" and the
  new module to its "Project structure" tree, like the existing jobs.
- If the implementation forced a detail the spec doesn't cover, report
  it rather than deciding it silently.

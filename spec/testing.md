# Testing

This document covers the project's testing conventions: what gets
tested, with what tooling, and where tests live. It's cross-cutting
(applies across `db/`, `ingest/`, `control/backend/` and, eventually,
`control/frontend/`), same status as `CLAUDE.md` itself — review it
before adding tests anywhere in the project, not just when a specific
module's spec mentions testing.

## Scope — decided: unit tests for pure transform/validation logic first

No test exists in the project yet. Rather than build a full testing
pyramid (integration tests against a real database, API-level tests,
frontend tests) before there's a clear need, start with the cheapest,
highest-signal kind: **unit tests for pure functions with no external
dependencies** (no network, no database) that already contain fiddly,
easy-to-get-wrong logic — exactly the kind of detail this project has
already had real surprises with (AEMET's decimal comma, its
`Ip`/`Acum` precipitation sentinels, its undocumented-until-verified
6-month date range limit).

Concrete first candidates:

- `ingest/stations.py`'s `parse_coordenada` (AEMET's `GGMMSSH`
  coordinate format → decimal degrees, including hemisphere sign) —
  see `spec/ingest/STATIONS.md`.
- `ingest/daily_values.py`'s comma-decimal parsing and `prec` sentinel
  handling (`Ip`/`Acum` → `NULL` in `precipitation_mm`, raw value kept
  in `precipitation_raw`) — see `spec/ingest/DAILY_VALUES.md`. Covers
  `run_import_all_stations` too, once implemented: it reuses the same
  `transform()` as `run_import` unchanged (see `spec/ingest/DAILY_VALUES.md`,
  "Import mode: all stations at once"), so it needs no test of its
  own beyond this one.
- `control/backend/modules/jobs/`'s (once implemented) validation:
  `date_from <= date_to` and the `SCHEDULER_MAX_DATE_RANGE` check —
  see `spec/control/module/jobs.md`.

**Why not more yet:** integration tests (DAO layers against a real
Postgres, FastAPI `TestClient`, frontend component tests) need
infrastructure this single-developer internal tool doesn't have yet
(a test database lifecycle, fixtures, possibly CI) — same reasoning
already applied when rejecting APScheduler/Celery for the job worker
(`spec/ingest/general.md`): don't add infrastructure without a clear
need. Revisit once integration-level bugs actually show up, or the
codebase grows enough to justify the setup cost.

## Known exceptions: database-dependent correctness

Some behavior is hard to fully trust by reading the code alone — it
only really holds if the database enforces it. These are integration
tests (a real Postgres, not mocked), the deliberate exceptions to
"unit tests only for now" above:

- **The job worker's claim logic** (`spec/ingest/general.md`):
  `FOR UPDATE SKIP LOCKED` job claiming — a candidate for a test with
  two concurrent claims racing for the same `pending` row.
- **`climatological_values` upsert idempotency on overlapping imports**
  (`spec/ingest/DAILY_VALUES.md`, "Load strategy"): re-importing a date
  range that overlaps already-stored rows must **update** them, never
  insert a duplicate. This is structurally guaranteed by the table's
  composite primary key (`station_code`, `date`) plus
  `UPSERT_SQL`'s `ON CONFLICT (station_code, date) DO UPDATE` — but
  "structurally guaranteed by a constraint plus a query" is exactly the
  kind of claim that's worth a real test against a real constraint,
  not just a reading of the SQL. See
  `ingest/tests/integration/test_daily_values.py`: inserts a row via
  `UPSERT_SQL`, upserts the same `(station_code, date)` again with
  different values, asserts exactly one row exists with the new
  values.

## Tooling and layout — decided: pytest, one suite per module

- **pytest**, consistent with the rest of the stack (Python-first
  project, see `CLAUDE.md`).
- Each independently-deployable module keeps its own tests, following
  the same independence already established for
  dependencies/virtual environments (`CLAUDE.md`, "Project
  structure"): `ingest/tests/`, `control/backend/tests/`, etc. `pytest`
  is added as a dependency to that module's own `requirements.txt`
  (e.g. `ingest/requirements.txt`) — there's no project-wide test
  runner or shared test dependency file, same as there's no shared
  `requirements.txt`.
- **Naming:** `test_<module>.py`, mirroring the file under test (e.g.
  `ingest/tests/test_stations.py` for `ingest/stations.py`).
- **Integration tests live in `<module>/tests/integration/` — decided.**
  Separated from the DB-free unit tests (previous bullet) so CI can
  run each group with the infrastructure it actually needs — a plain
  `pytest <module>/tests/` for the fast/no-DB job, a targeted
  `pytest <module>/tests/integration/` for the job with a Postgres
  service (see "Continuous integration" below) — instead of one mixed
  suite where every run pays for the slowest test's setup.

## Continuous integration — decided: GitHub Actions, one job per module

- `.github/workflows/tests.yml` runs on **every push (any branch) and
  every pull request, unconditionally** — no path filter. A change
  that isn't in a test file can still break one (e.g. editing
  `ingest/stations.py` without touching `ingest/tests/`), so scoping
  the trigger to test-file changes would miss exactly the regressions
  this exists to catch.
- **One job per module for unit tests**, mirroring "one suite per
  module" above: `ingest-tests` installs `ingest/requirements.txt` and
  runs `pytest ingest/tests/ --ignore=ingest/tests/integration`;
  `backend-tests` installs `control/backend/requirements.txt` and runs
  `pytest tests/` with `control/backend/` as the working directory
  (needed for its `modules.*`-style imports to resolve, same as
  running it locally). Each job only installs its own module's
  dependencies, same independence criterion as everywhere else in the
  project. No `services:` Postgres container here — these stay
  DB-free, mocked/monkeypatched DAOs and pure transform functions (see
  "Scope" above).
- **A separate job per module for integration tests, with a Postgres
  service — decided.** `ingest-integration-tests`: brings up a
  `postgres:16` service (same image as `docker-compose.yml`), installs
  `db/requirements.txt` + `ingest/requirements.txt`, runs `python
  db/migrate.py upgrade` against it (so `stations`/`climatological_values`
  exist — same schema-build path as everywhere else, no hand-written
  test schema), then `pytest ingest/tests/integration/`. Kept separate
  from `ingest-tests` so the fast unit job doesn't pay for Postgres
  startup, and so a Postgres outage/flake in CI doesn't fail the
  unit-test signal.

## Pending decisions

- Whether/when to add integration tests beyond the two "Known
  exceptions" above (DAO layers, FastAPI `TestClient`, frontend
  component tests) — each would need its own module's CI job extended
  with a Postgres service the same way `ingest-integration-tests` now
  is.

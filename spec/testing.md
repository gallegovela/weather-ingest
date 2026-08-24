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
- `ingest/daily_values.py`'s (once implemented) comma-decimal parsing
  and `prec` sentinel handling (`Ip`/`Acum` → `NULL` in
  `precipitation_mm`, raw value kept in `precipitation_raw`) — see
  `spec/ingest/DAILY_VALUES.md`.
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

## Known exception: the job worker's claim logic

`FOR UPDATE SKIP LOCKED` job claiming (`spec/ingest/general.md`) is
concurrency logic that's hard to fully trust by reading the code
alone. Once the job worker is implemented, this is a good candidate
for an early **integration** test against a real Postgres (two
concurrent claims racing for the same `pending` row), ahead of the
"unit tests only for now" scope above — the one deliberate exception.

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

## Pending decisions

- Whether/when to add integration tests beyond the job worker's claim
  logic exception above (DAO layers, FastAPI `TestClient`, frontend
  component tests).
- Whether a CI pipeline is ever needed to run tests automatically —
  none exists today; tests are run locally by hand.

---
name: run-tests
description: How to run this project's tests (ingest unit/integration, control/backend, control/frontend lint/build) — which suite covers which part of the code, with which virtual environment, and what to do when an environment or database isn't available. Use after changing code, before finishing a task.
---

# Running the tests

The project has no shared test runner: each module has its own suite
and its own dependencies (`spec/testing.md`). Run the suite of every
module you touched — and of any module that imports what you touched
(e.g. `ingest/` code used by the job worker).

All commands below are run from the repository root unless a `cd` says
otherwise. They are the same ones `.github/workflows/tests.yml` runs in
CI.

## Which suite for which change

| You changed | Run |
|---|---|
| `ingest/` | ingest unit tests; ingest integration tests if you touched SQL or `db.py` (see below) |
| `db/migrations/` | ingest integration tests (they run against the migrated schema) |
| `control/backend/` | backend unit tests |
| `control/frontend/` | frontend lint + build |
| `spec/` only | nothing |

## ingest — unit tests (no database)

```
python -m venv .venv                                  # only if .venv/ doesn't exist
.venv/bin/pip install -q -r ingest/requirements.txt   # only if pytest isn't installed
DATABASE_URL=postgresql+psycopg://unused:unused@localhost:1/unused \
  .venv/bin/python -m pytest ingest/tests/ --ignore=ingest/tests/integration -q
```

- **`DATABASE_URL` must be set even though these tests never connect.**
  `ingest/config.py` raises `RuntimeError: DATABASE_URL is not set` at
  import time, and every module under test imports it through
  `ingest/db.py`. Locally the project root's `.env` provides it; in a
  fresh checkout (CI, the issue pipeline's runner) there is no `.env`,
  so pass a dummy value as above. Any syntactically valid URL works:
  nothing connects to it.
- Always pass `--ignore=ingest/tests/integration`: without it pytest
  also collects the integration tests, which need a real database.

## ingest — integration tests (real Postgres)

```
.venv/bin/pip install -q -r db/requirements.txt -r ingest/requirements.txt
.venv/bin/python db/migrate.py upgrade
.venv/bin/python -m pytest ingest/tests/integration/ -q
```

- They need `DATABASE_URL` pointing at a **disposable development
  database** (locally: the `postgres` service of `docker-compose.yml`,
  started with `docker compose up -d postgres`, with the credentials
  already in `.env`). The tests roll back everything they write, but
  `migrate.py upgrade` does change the schema.
- **Never run them against any other database, and never start
  `docker compose` yourself on a shared or server machine** (e.g. the
  issue pipeline's self-hosted runner, which shares a host with the
  deployed stack): you could hit the production database or clash with
  the running containers. If there is no `.env`/`DATABASE_URL` for a
  development database, skip them and say so in your summary — CI
  (`ingest-integration-tests` in `tests.yml`) runs them on every push
  with its own throwaway Postgres.

## control/backend — unit tests

```
cd control/backend
python -m venv .venv                          # only if .venv/ doesn't exist
.venv/bin/pip install -q -r requirements.txt  # only if pytest isn't installed
.venv/bin/python -m pytest tests/ -q
```

- Must run with `control/backend/` as the working directory: the code
  imports `modules.*` / `core.*` relative to it.
- It has its own `.venv/`, separate from the root one — don't install
  backend dependencies into the root `.venv/` or vice versa.
- No database needed: DAOs are monkeypatched (see existing tests in
  `control/backend/tests/` for the pattern).

## control/frontend — lint and build

There are no frontend tests yet (`spec/testing.md`, "Pending
decisions"); lint and a production build are the check:

```
cd control/frontend
npm ci              # only if node_modules/ doesn't exist
npm run lint
npm run build
```

`npm run build` writes `dist/`, which is gitignored — no cleanup
needed.

## Reporting

- Report each suite you ran with its result (e.g. `ingest unit: 15
  passed`), and each relevant suite you couldn't run with the reason.
- A failing test is never "fixed" by deleting it, skipping it or
  loosening its assertion. Fix the code, or, if the test itself
  encodes behavior the spec has since changed, update it and say so.
- Don't leave generated files behind: `.venv/`, `__pycache__/`,
  `node_modules/` and `dist/` are gitignored, anything else you create
  while testing must be removed.

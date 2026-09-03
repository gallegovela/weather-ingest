# Deployment

This document covers continuous deployment: how a commit on `main`
ends up running on the target server. It's cross-cutting (it deploys
the whole `docker-compose.yml` stack — `db/` migrations aren't run by
it, see "Design notes" below), same status as `CLAUDE.md` itself —
review it before touching anything deployment-related, not just the
workflow file itself.

## Goal — decided: continuous deployment on push to `main`

Every commit on `main` is deployed automatically to the target
server, no manual step. Implemented as a GitHub Actions workflow
(`.github/workflows/deploy.yml`, not created in this stage — see
"Implementation" below).

## Trigger — decided: every push to `main`, no path filter

`on: push: branches: [main]`. Same criterion as
`spec/testing.md`'s CI trigger: a change anywhere can require a
rebuild, and `docker-compose build --no-cache` rebuilds the whole
stack regardless of which files changed, so scoping the trigger to a
subset of paths would only add complexity without saving work.

## Runner — decided: `ionos-l1-docker`

A self-hosted runner distinct from `ionos-l1-claude` (used by
`.github/workflows/issue-pipeline.yml`): this workflow needs access to
Docker and to the server's persistent filesystem, not to the `claude`
CLI.

## Secret — decided: `SOURCE_PATH`

A new repository secret, `SOURCE_PATH`: the absolute path on the
runner's host where the persistent checkout lives. Not the ephemeral
Actions workspace (which is wiped between runs) — the deploy flow
needs a directory that survives across runs so it can `git pull`
instead of cloning from scratch every time. This is also why the
workflow uses raw `git` commands instead of `actions/checkout`, which
only knows how to check out into the ephemeral workspace.

## Flow — decided

1. Check whether `SOURCE_PATH` exists (`test -d`).
2. If it exists: `git -C "$SOURCE_PATH" pull`.
3. If it doesn't: `git clone --branch main <repo-url> "$SOURCE_PATH"`.
4. `cd "$SOURCE_PATH"` and run
   `docker-compose down && docker-compose build --no-cache && docker-compose up -d`.

## Design notes

- **`git` authentication on the runner (SSH vs. HTTPS token) is out of
  this spec's scope**: it's host-level setup on the self-hosted
  runner (an existing deploy key, or a token), not something the
  workflow file itself decides or manages.
- **`.env` in `SOURCE_PATH` is assumed to already exist on the
  server** and is left untouched by this flow. `docker-compose`
  needs it (production `DATABASE_URL`, etc.) and it's gitignored
  (`CLAUDE.md`, "Environment variables"), so it can't come from
  `git pull`/`git clone` — it must be provisioned on the server ahead
  of the first deploy, outside this workflow's responsibility.
- **`db/` migrations are not run by this workflow.** Deployment only
  brings up the containers already defined in `docker-compose.yml`;
  applying pending migrations (`python db/migrate.py upgrade`, see
  `spec/db/general.md`) against the production database stays a
  separate, manual step for now.
- **Concurrent runs — decided: queue, don't cancel.** Two pushes to
  `main` in close succession should not cancel a deploy that's
  mid-flight (a cancelled run could leave the stack `down` with a
  build still in progress). `concurrency: group: deploy,
  cancel-in-progress: false` queues the second run instead.
- **No rollback on build failure.** If `docker-compose build
  --no-cache` fails, the stack stays down (already stopped by the
  preceding `docker-compose down`) until the next successful push —
  consistent with the project's existing "no retries" stance (e.g.
  `spec/ingest/STATIONS.md`), applied here to deploys instead of
  ingestion jobs.

## Implementation

Out of scope for this document: once this spec is agreed, the actual
`.github/workflows/deploy.yml` implementing the flow above is added as
a separate step.

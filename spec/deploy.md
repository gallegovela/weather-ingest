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

0. Point the repo URL at the HTTPS remote authenticated with the
   job's own `GITHUB_TOKEN` (see "Design notes") — no key to unlock.
1. Check whether `SOURCE_PATH` exists (`test -d`).
2. If it exists: `git -C "$SOURCE_PATH" pull`.
3. If it doesn't: `git clone --branch main <repo-url> "$SOURCE_PATH"`.
4. `cd "$SOURCE_PATH"` and run
   `docker-compose down && docker-compose build --no-cache && docker-compose up -d`.

## Design notes

- **`git` authentication on the runner — decided: the job's own
  `GITHUB_TOKEN`, over HTTPS.** No SSH key, no `SSH_KEY_PASSPHRASE`
  secret, no `.github/actions/setup-ssh-and-git`: `SOURCE_PATH` is
  cloned/pulled from `https://x-access-token:${GITHUB_TOKEN}@github.com/<repo>.git`,
  where `GITHUB_TOKEN` is the token GitHub Actions generates
  automatically for each job run (`github.token` / `secrets.GITHUB_TOKEN`,
  no provisioning needed). Replaces the previous design, which reused
  `setup-ssh-and-git` (still used by `issue-pipeline.yml`'s
  `preparation`/`implementation` stages — see `spec/issue_pipeline.md`
  for that workflow's own migration to the same token-based approach).
- **`permissions: contents: read`, declared explicitly.** The job
  only needs read access to clone/pull; declaring it instead of
  relying on the repository's default permissions makes the
  requirement visible in the workflow file itself.
- **`.env` in `SOURCE_PATH` is assumed to already exist on the
  server** and is left untouched by this flow. `docker-compose`
  needs it (production `DATABASE_URL`, etc.) and it's gitignored
  (`CLAUDE.md`, "Environment variables"), so it can't come from
  `git pull`/`git clone` — it must be provisioned on the server ahead
  of the first deploy, outside this workflow's responsibility.
- **`SOURCE_PATH` must be group-writable by the runner container's
  UID/GID.** `ionos-l1-docker` is a Docker container (image
  `gallegovela-github-selfhosted-runners/deploy-docker-runner`) that
  bind-mounts the host's `/var/www` straight through (no UID
  remapping) and runs its process as `runner`, UID:GID `1001:1001`.
  Bind mounts resolve permissions against that numeric host UID/GID,
  so if `SOURCE_PATH` (or its `.git/config`) is `root`-owned with no
  group/other write bit — e.g. it was seeded by an earlier manual
  clone done as `root` — the container's `git -C "$SOURCE_PATH"
  remote set-url` / `pull` can't lock `.git/config` and the step fails
  with `error: could not lock config file .git/config: Permission
  denied` (the incident reported in issue #13). This isn't something
  the workflow can fix for itself: on the host, `SOURCE_PATH` must be
  prepared out of band, before the first automated deploy, the same
  way the `.env` file itself is provisioned ahead of time — owner
  stays `root`, group set to the runner's GID with write access:
  ```
  chown -R root:1001 "$SOURCE_PATH"
  chmod -R g+w "$SOURCE_PATH"
  ```
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

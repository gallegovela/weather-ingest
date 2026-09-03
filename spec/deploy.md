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

0. Unlock the deployment SSH key (`.github/actions/setup-ssh-and-git`,
   reused with remote/identity configuration skipped — see "Design
   notes").
1. Check whether `SOURCE_PATH` exists (`test -d`).
2. If it exists: `git -C "$SOURCE_PATH" pull`.
3. If it doesn't: `git clone --branch main <repo-url> "$SOURCE_PATH"`.
4. `cd "$SOURCE_PATH"` and run
   `docker-compose down && docker-compose build --no-cache && docker-compose up -d`.

## Design notes

- **`git` authentication on the runner — decided: reuse
  `.github/actions/setup-ssh-and-git`.** Same pattern already used by
  `issue-pipeline.yml`'s `preparation`/`implementation` stages: the
  composite action unlocks the deploy SSH key (`~/.ssh/id_ed25519`,
  passphrase in the `SSH_KEY_PASSPHRASE` secret) via `ssh-agent`, so
  `git clone`/`git pull` over the SSH remote work unattended. Invoked
  as step 0 of the `deploy` job, before touching `SOURCE_PATH`.
- **Host prerequisite: the deploy key must also be present on
  `ionos-l1-docker`.** `setup-ssh-and-git` assumes the key is already
  on disk at `~/.ssh/id_ed25519` — true today for `ionos-l1-claude`,
  and now required for `ionos-l1-docker` too. Provisioning the key on
  that host is still host-level setup, out of this workflow's scope,
  but it's now an explicit prerequisite instead of an omission.
- **Reuse mismatch: `setup-ssh-and-git` needs an opt-out for
  remote/identity configuration.** The action also runs `git remote
  set-url origin ...` and `git config user.name/email` against the
  repo already checked out in the current working directory — valid
  in `preparation`/`implementation`, which run after
  `actions/checkout`. `deploy.yml` has no `actions/checkout` (it
  operates directly on `SOURCE_PATH`, which doesn't exist yet on the
  first run) and never commits, so those two commands would fail
  (`fatal: not a git repository`) if run as-is. Decision: give the
  action an optional input (e.g. `configure-remote`, default `true`)
  that `deploy.yml` sets to `false` to skip that part and only unlock
  the SSH agent. Changing the action's interface is implementation,
  not this spec — but it's documented here because `deploy.yml`
  depends on this parameterized reuse instead of duplicating the
  `ssh-agent`/`ssh-add` logic inline.
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

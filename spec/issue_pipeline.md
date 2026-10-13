# Issue pipeline

This document covers `.github/workflows/issue-pipeline.yml`: the
label-gated automation that lets `claude` (run on the `ionos-l1-claude`
self-hosted runner, authenticated via the `CLAUDE_CODE_OAUTH_TOKEN`
organization secret) work an issue end to end, from a spec proposal to
an open pull request. Same status as `CLAUDE.md` itself — review it
before touching the workflow file, not just when a stage's behavior
looks relevant.

## Stages — decided: four label-gated jobs, sharing one permission gate

- **`documentation`**: reads the issue and its comment thread, proposes
  a `spec/` change plan, posts it as an issue comment. No writes — no
  checkout side effects beyond reading.
- **`preparation`**: creates (or reuses) branch `issue-<n>`, applies the
  `spec/` changes from the agreed plan, commits and pushes. Does not
  touch code outside `spec/`.
- **`implementation`**: on `issue-<n>`, implements the code that
  fulfills that spec, following the order set in `CLAUDE.md` (`db` ->
  `ingest` -> `control/backend` -> `control/frontend`). Commits and
  pushes.
- **`merge`**: opens a pull request from `issue-<n>` to the repository's
  default branch.

Each stage runs when its label is added to the issue (`issues:
labeled`), or re-runs on a new comment while its label is still present
(`issue_comment: created`, gated by `contains(github.event.issue.labels.*.name,
'<stage>')`) — so answering a clarifying question in the thread re-runs
the *current* stage without removing/re-adding the label.

- **`check-permission` gate — decided: shared by every stage via
  `needs`.** Hand-invoking the `claude` CLI (instead of the
  `anthropics/claude-code-action` marketplace action) means the
  built-in write-access check that action provides is lost; this job
  adds it back once, calling `gh api
  repos/<repo>/collaborators/<actor>/permission` and exposing
  `outputs.allowed`, which every stage's `if:` checks alongside its own
  label condition.

## Authentication for `preparation`/`implementation` — decided: the `GH_TOKEN` organization secret, over HTTPS

Committing and pushing branch `issue-<n>` no longer unlocks a
deployment SSH key via `.github/actions/setup-ssh-and-git`. Instead,
each stage points `origin` at the HTTPS remote authenticated with the
`GH_TOKEN` organization secret — a personal access token provisioned
once at the organization level, not generated per job run — then sets
the commit identity, replacing the two things `setup-ssh-and-git` used
to do:

```
git remote set-url origin "https://x-access-token:${GH_TOKEN}@github.com/${GITHUB_REPOSITORY}.git"
git config user.name "Claude (automated)"
git config user.email "noreply@anthropic.com"
```

- **Why not the job's own `github.token`/`GITHUB_TOKEN`.** Its
  identity is a GitHub Actions App install that can never carry the
  `workflows` permission, no matter how `permissions:` is set on the
  workflow or the organization — a fixed platform restriction, not a
  configuration gap. Any commit touching `.github/workflows/**` (e.g.
  the `docker-compose` -> `docker compose` fix tracked by this same
  issue) is rejected on push with "refusing to allow a GitHub App to
  create or update workflow ... without `workflows` permission".
  `GH_TOKEN` is a regular PAT, so it carries no such restriction — and
  as a side effect, pushes to `issue-<n>` are made by a "normal"
  identity again, so `tests.yml` goes back to triggering automatically
  on them (`on: push`, no branch filter — see `spec/testing.md`).
- **Scope of the change.** Only the "Configure git remote and
  identity" step of `preparation`/`implementation` (the single step
  that does `git push`) uses `GH_TOKEN`. `check-permission` and the
  "Post result comment" step of all four stages, plus the whole
  `merge` stage, keep using `github.token` for their `gh` calls
  (commenting on the issue, opening the pull request) — none of those
  need the `workflows` permission, and none have shown any problem.
- **`.github/actions/setup-ssh-and-git` is retired.** No caller left in
  this repository once `preparation`/`implementation` stop using it
  (see `spec/deploy.md` for `deploy.yml`'s own, separate migration to
  the same token-based approach — that workflow never shared
  `setup-ssh-and-git`'s remote/identity configuration, only its SSH
  agent unlock).

## Pending decisions

None.

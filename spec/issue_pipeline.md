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

## GitHub token authentication — decided: `GITHUB_TOKEN` set once, at workflow level

Two independent things need GitHub authentication in this workflow,
not just one:

1. **`git push`** in `preparation`/`implementation`: committing and
   pushing branch `issue-<n>` no longer unlocks a deployment SSH key
   via `.github/actions/setup-ssh-and-git`. Instead, the stage points
   `origin` at the HTTPS remote authenticated with the token GitHub
   Actions generates automatically for the job run (`github.token` /
   `secrets.GITHUB_TOKEN` — no secret to provision, no passphrase),
   then sets the commit identity, replacing the two things
   `setup-ssh-and-git` used to do:

   ```
   git remote set-url origin "https://x-access-token:${GITHUB_TOKEN}@github.com/${GITHUB_REPOSITORY}.git"
   git config user.name "Claude (automated)"
   git config user.email "noreply@anthropic.com"
   ```

2. **`gh`**, called by every stage — either directly by a workflow
   step (`check-permission`'s collaborator check, "Post result
   comment") or by `claude` itself, inside the prompt's own `Bash(gh
   issue view:*)` / `Bash(gh pr create:*)` tool calls
   (`documentation`, `preparation`, `implementation` all re-read the
   issue thread this way; `merge` opens the PR this way). `gh` reads
   `GH_TOKEN`/`GITHUB_TOKEN` from the environment; if the step running
   `claude` doesn't have it, `gh` fails inside the tool call the same
   way it would on a bare shell.

**Incident (issue #13):** `GITHUB_TOKEN` was only exported in the
steps that call `git`/`gh` directly (`check-permission`, "Configure
git remote and identity", `merge`'s "Run Claude", "Post result
comment"), not in the "Run Claude" step of `documentation`,
`preparation` and `implementation`. Since `claude` runs `gh issue
view` as part of its own tool calls in those three stages, and that
step had no token in its environment, `gh` had nothing to authenticate
with and the stage failed before it could read the issue at all.

**Fix — decided: declare `GITHUB_TOKEN: ${{ github.token }}` once, in
the workflow-level `env:` block**, alongside `CLAUDE_CODE_OAUTH_TOKEN`.
Every job and every step inherits it automatically, covering both uses
above (`gh` auth and the git remote URL) without having to remember to
repeat it per stage. The per-step declarations that existed only to
work around the gap (`GH_TOKEN`/`GITHUB_TOKEN` re-declared in
`check-permission`, "Configure git remote and identity", `merge`'s
"Run Claude", "Post result comment") are removed as redundant now that
the value is already in the environment from the workflow level.

- **`permissions: contents: write`, up from `contents: read`.**
  Required for the default `GITHUB_TOKEN` to push at all; `read` was
  enough while pushing relied on the SSH key's own access instead of
  the token's scope. Declared at the workflow level (same as today),
  so it also applies to `documentation`/`merge`, which don't need it
  but aren't harmed by having it.
- **`.github/actions/setup-ssh-and-git` is retired.** No caller left in
  this repository once `preparation`/`implementation` stop using it
  (see `spec/deploy.md` for `deploy.yml`'s own, separate migration to
  the same token-based approach — that workflow never shared
  `setup-ssh-and-git`'s remote/identity configuration, only its SSH
  agent unlock).

## Pending decisions

- **`tests.yml` no longer runs automatically on `issue-<n>` pushes.**
  Pushes/PRs authenticated with the default `GITHUB_TOKEN` don't
  trigger other workflows (GitHub's own anti-recursion restriction).
  Today, `preparation`/`implementation` push with the SSH key — a
  "normal" identity — so those pushes to `issue-<n>` do trigger
  `tests.yml` (`on: push`, no branch filter, see `spec/testing.md`).
  Moving to `GITHUB_TOKEN` loses that automatic run until someone
  triggers it manually or a PR is opened from outside the bot. This
  doesn't block deployment (`deploy.yml` still triggers normally, since
  the push to `main` at merge time is made by a human), but it is a CI
  coverage regression, accepted knowingly for now: to be revisited
  together with the separate, already-open issue about reworking these
  tests, not solved here.

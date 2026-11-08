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

## GitHub token authentication — decided: `GH_TOKEN` secret, set once at workflow level

Every interaction with GitHub in this workflow — git pushes, issue
comments, PR creation, API calls — authenticates with an API token
stored in the **`GH_TOKEN` repository/organization secret**
(`secrets.GH_TOKEN`), not with the token GitHub Actions generates
automatically for each run (`github.token` / `secrets.GITHUB_TOKEN`).
The secret name can't start with `GITHUB_` (reserved by GitHub).

Two independent things need it:

1. **`git push`** in `preparation`/`implementation`: every
   `actions/checkout` step passes `token: ${{ secrets.GH_TOKEN }}`, so
   checkout persists that token as the credential for every later git
   fetch/push on the checkout (instead of the default `github.token`,
   which checkout would otherwise persist and which would take
   precedence over credentials embedded in a remote URL). No `git
   remote set-url` is needed anymore; the stage only sets the commit
   identity:

   ```
   git config user.name "Claude (automated)"
   git config user.email "noreply@anthropic.com"
   ```

   `documentation`/`merge` pass the same `token:` for consistency,
   even though they don't push.

2. **`gh`**, called by every stage — either directly by a workflow
   step (`check-permission`'s collaborator check, "Post result
   comment") or by `claude` itself, inside the prompt's own `Bash(gh
   issue view:*)` / `Bash(gh pr create:*)` tool calls
   (`documentation`, `preparation`, `implementation` all re-read the
   issue thread this way; `merge` opens the PR this way). `gh` reads
   `GH_TOKEN` from the environment (it takes precedence over
   `GITHUB_TOKEN`); if the step running `claude` doesn't have it, `gh`
   fails inside the tool call the same way it would on a bare shell.

**Declared once, in the workflow-level `env:` block**
(`GH_TOKEN: ${{ secrets.GH_TOKEN }}`), alongside
`CLAUDE_CODE_OAUTH_TOKEN`, so every job and every step inherits it
without having to remember to repeat it per stage.

**Incident (issue #13), why it's workflow-level:** the token used to be
exported only in the steps that call `git`/`gh` directly
(`check-permission`, "Configure git remote and identity", `merge`'s
"Run Claude", "Post result comment"), not in the "Run Claude" step of
`documentation`, `preparation` and `implementation`. Since `claude`
runs `gh issue view` as part of its own tool calls in those three
stages, and that step had no token in its environment, `gh` had nothing
to authenticate with and the stage failed before it could read the
issue at all.

- **Required token permissions.** Fine-grained token scoped to this
  repository: *Contents* read/write (push `issue-<n>`), *Issues*
  read/write (read threads, post result comments), *Pull requests*
  read/write (`gh pr create`), *Metadata* read (collaborator
  permission check). A classic token needs the `repo` scope.
- **`permissions: contents: read`, down from `contents: write` /
  `issues: write` / `pull-requests: write`.** `permissions:` only
  governs the auto-generated `github.token`, which nothing in this
  workflow uses anymore; kept at the minimum so a missing `GH_TOKEN`
  fails loudly instead of silently falling back to a write-capable
  token.
- **`.github/actions/setup-ssh-and-git` is retired.** No caller left in
  this repository (see `spec/deploy.md` for `deploy.yml`'s own
  migration to the same `GH_TOKEN` secret).
- **`tests.yml` runs again on `issue-<n>` pushes.** Pushes/PRs
  authenticated with the default `github.token` don't trigger other
  workflows (GitHub's anti-recursion restriction), which was a known
  CI coverage regression while this workflow pushed with it. Pushes
  made with `GH_TOKEN` count as a regular identity, so they trigger
  `tests.yml` (`on: push`, no branch filter, see `spec/testing.md`)
  like any human push.

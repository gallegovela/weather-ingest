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

## GitHub token authentication — decided: `GH_TOKEN` per job, every GitHub call through `gh`

Every interaction with GitHub in this workflow — git fetch/push, issue
comments, PR creation, API calls — goes through **`gh`**, authenticated
with an API token stored in the **`GH_TOKEN` repository/organization
secret** (`secrets.GH_TOKEN`), not with the token GitHub Actions
generates automatically for each run (`github.token` /
`secrets.GITHUB_TOKEN`).

**Declared in every job's own `env:`** (`check-permission` and the four
stages), not at workflow level:

```
env:
  GH_TOKEN: ${{ secrets.GH_TOKEN }}
```

`GH_TOKEN` is the variable `gh` reads, so no other variable is needed.
Every step in the job inherits it, so no step needs to re-declare it.

How each kind of interaction uses it:

1. **`gh` directly** — `check-permission`'s `gh api` collaborator
   check and every stage's "Post result comment" (`gh issue comment`).
2. **`gh` inside `claude`'s tool calls** — `Bash(gh issue view:*)` in
   every stage, `Bash(gh pr create:*)` in `merge`. These run in the
   "Run Claude" step's environment, which inherits the job's `env:`.
3. **git, via `gh` as credential helper** — `actions/checkout` does the
   initial fetch with `token: ${{ secrets.GH_TOKEN }}` and
   `persist-credentials: false` (otherwise it leaves its own
   `extraheader` credential in `.git/config`, which would take
   precedence over the helper). Then, in every stage that runs git
   afterwards (`preparation`, `implementation`, `merge`), a "Configure
   git" step installs the same helper `gh auth setup-git` would, but
   scoped to the checkout (`--local`) instead of the self-hosted
   runner's global config:

   ```
   git config --local credential.https://github.com.helper ''
   git config --local --add credential.https://github.com.helper '!gh auth git-credential'
   git config user.name "Claude (automated)"
   git config user.email "noreply@anthropic.com"
   ```

   The empty first entry resets any helper inherited from global
   config. Every later `git fetch`/`git push` (including `claude`'s own
   `Bash(git *)` calls) asks `gh` for credentials, which answers with
   `GH_TOKEN`. `documentation` doesn't run git after checkout, so it
   skips this step.

**Incident (issue #13), why every job declares it:** the token used to
be exported only in the steps that call `git`/`gh` directly, not in the
"Run Claude" step of `documentation`, `preparation` and
`implementation`. Since `claude` runs `gh issue view` as part of its
own tool calls, that step had no token in its environment and the stage
failed before it could read the issue at all. Declaring it at job level
covers every step of every job.

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
  migration to the same `GH_TOKEN` secret and `gh`-based access).
- **`tests.yml` runs again on `issue-<n>` pushes.** Pushes/PRs
  authenticated with the default `github.token` don't trigger other
  workflows (GitHub's anti-recursion restriction), which was a known
  CI coverage regression while this workflow pushed with it. Pushes
  made with `GH_TOKEN` count as a regular identity, so they trigger
  `tests.yml` (`on: push`, no branch filter, see `spec/testing.md`)
  like any human push.

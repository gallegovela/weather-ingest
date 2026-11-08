# Issue pipeline

This document covers `.github/workflows/issue-pipeline.yml`: the
label-gated automation that lets `claude` (run on the `ionos-l1-claude`
self-hosted runner, authenticated via the `CLAUDE_CODE_OAUTH_TOKEN`
organization secret) work an issue end to end, from a spec proposal to
an open pull request. Same status as `CLAUDE.md` itself — review it
before touching the workflow file or the agent definitions it uses
(`.claude/agents/`), not just when a stage's behavior looks relevant.

## Stages — decided: four label-gated jobs, sharing one permission gate

- **`documentation`** (agent: `architect`): reads the issue and its
  comment thread, proposes a `spec/` change plan, posts it as an issue
  comment. No writes.
- **`preparation`** (agent: `architect`): creates (or reuses) branch
  `issue-<n>`, applies the `spec/` changes from the agreed plan; the
  workflow then commits and pushes them. Must not touch anything
  outside `spec/`.
- **`implementation`** (agent: `developer`): on `issue-<n>`, implements
  the code that fulfills that spec, following the order set in
  `CLAUDE.md` (`db` -> `ingest` -> `control/backend` ->
  `control/frontend`); the workflow then commits and pushes.
- **`merge`** (no agent, plain bash): opens a pull request from
  `issue-<n>` to the repository's default branch.

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

## Agents — decided: one Claude Code agent per role, in `.claude/agents/`

The stage prompts, the model and the tool set live in Claude Code
agent definitions, not in the workflow file. The workflow only runs
`claude -p "<stage request>" --agent <name>`, where the stage request
is a short line naming the stage, the issue number and where the issue
thread was saved (see "GitHub access" below); everything the agent has
to do for that stage is in its own definition.

| Agent | File | Model | Tools | Stages |
|---|---|---|---|---|
| `architect` | `.claude/agents/architect.md` | `claude-opus-5-5` | Read, Grep, Glob, Write, Edit | `documentation`, `preparation` |
| `developer` | `.claude/agents/developer.md` | `claude-sonnet-5-5` | Read, Grep, Glob, Write, Edit, Bash | `implementation` |

- **Changing a stage's behavior or model = editing the agent file**
  (`model:` in its frontmatter), never the workflow.
- **One agent, two stages (`architect`).** Its definition holds the
  instructions for both `documentation` and `preparation`; the stage
  request tells it which one applies. In `documentation`, the workflow
  also passes `--disallowedTools "Write Edit"`.
- **`developer` has `Bash`** so it can run the project's unit tests
  (`spec/testing.md`) against its own changes. It has no GitHub
  credentials (see below), so it can't push or call the API.
- **Native Claude Code format, not a provider-neutral one.** Codex
  support was considered and deferred; if it's revisited, the agent
  definitions would need a neutral format plus a dispatcher script.
  Side effect of the native format: both agents are also available as
  subagents in interactive Claude Code sessions in this repository.
- **The workflow enforces each stage's write scope**, instead of
  trusting the prompt: `documentation` fails if the working tree has
  any change after the agent runs; `preparation` fails if any staged
  change is outside `spec/`.

## GitHub access — decided: only the workflow talks to GitHub, through `gh`

Agents never interact with GitHub. Every interaction — reading the
issue, git fetch/push, issue comments, PR creation, API calls — is a
workflow step running **`gh`** (or git with `gh` as credential helper),
authenticated with an API token stored in the **`GH_TOKEN`
repository/organization secret** (`secrets.GH_TOKEN`), not with the
token GitHub Actions generates automatically for each run
(`github.token` / `secrets.GITHUB_TOKEN`).

Flow of an agent stage:

1. **Before the agent:** a "Fetch issue thread" step saves the issue
   and its whole comment thread (`gh issue view` + `gh issue view
   --comments`) to `$RUNNER_TEMP/issue.md` — outside the checkout, so
   it can never be committed. The agent reads it from there.
2. **The agent** only reads/edits files in the checkout and ends with
   a reply (its final message), saved to `$RUNNER_TEMP/claude_output.txt`.
3. **After the agent:** the workflow validates the stage's write scope
   (see "Agents"), commits and pushes (`preparation`/`implementation`),
   and posts the agent's reply as an issue comment (`gh issue
   comment`, `if: always()`).

**`GH_TOKEN` is declared only in the `env:` of the steps that use
it**, never at job or workflow level, so it is never in the "Run
Claude" step's environment:

```
env:
  GH_TOKEN: ${{ secrets.GH_TOKEN }}
```

`GH_TOKEN` is the variable `gh` reads, so no other variable is needed.
This reverses the earlier job-level declaration, whose only reason was
the agent's own `gh` calls (incident in issue #13: `gh issue view`
inside "Run Claude" failed for lack of a token) — agents no longer
make any.

- **git, via `gh` as credential helper.** `actions/checkout` does the
  initial fetch with `token: ${{ secrets.GH_TOKEN }}` and
  `persist-credentials: false` (otherwise it leaves its own
  `extraheader` credential in `.git/config`, which would take
  precedence over the helper, and which the agent could use). Then, in
  `preparation`/`implementation`, a "Configure git" step installs the
  same helper `gh auth setup-git` would, but scoped to the checkout
  (`--local`) instead of the self-hosted runner's global config:

  ```
  git config --local credential.https://github.com.helper ''
  git config --local --add credential.https://github.com.helper '!gh auth git-credential'
  git config user.name "Claude (automated)"
  git config user.email "noreply@anthropic.com"
  ```

  The empty first entry resets any helper inherited from global
  config. The helper only works in steps that have `GH_TOKEN` in their
  environment (fetch branch, commit and push), so a `git push` from
  the agent's own `Bash` fails for lack of credentials.
- **Commit messages are set by the workflow**: `Update spec for #<n>
  (automated)` in `preparation`, `Implement #<n> (automated)` in
  `implementation`. A stage with no changes skips the commit.
- **`set -o pipefail` in "Run Claude".** The step pipes `claude` into
  `tee`; without `pipefail` a failing `claude` would still let the
  commit/push steps run.
- **Required token permissions.** Fine-grained token scoped to this
  repository: *Contents* read/write (push `issue-<n>`, compare
  branches), *Issues* read/write (read threads, post result comments),
  *Pull requests* read/write (`gh pr create`/`gh pr list`), *Metadata*
  read (collaborator permission check, default branch). A classic
  token needs the `repo` scope.
- **`permissions: contents: read`.** `permissions:` only governs the
  auto-generated `github.token`, which nothing in this workflow uses;
  kept at the minimum so a missing `GH_TOKEN` fails loudly instead of
  silently falling back to a write-capable token.
- **`.github/actions/setup-ssh-and-git` is retired.** No caller left in
  this repository (see `spec/deploy.md` for `deploy.yml`'s own
  migration to the same `GH_TOKEN` secret and `gh`-based access).
- **`tests.yml` runs on `issue-<n>` pushes.** Pushes authenticated with
  the default `github.token` don't trigger other workflows (GitHub's
  anti-recursion restriction); pushes made with `GH_TOKEN` count as a
  regular identity, so they trigger `tests.yml` (`on: push`, no branch
  filter, see `spec/testing.md`) like any human push.

## `merge` stage — decided: plain bash, no agent

Opening the PR is mechanical, so it doesn't run `claude` at all (and
needs no checkout: everything goes through the API, with `GH_REPO` set
so `gh` knows the repository). Steps:

1. Resolve the default branch (`gh repo view --json defaultBranchRef`).
2. If an open PR from `issue-<n>` already exists (`gh pr list --head`),
   don't open another one: the result comment links the existing one.
   Makes re-runs (a new comment while `merge` is still labeled) safe.
3. Otherwise `gh pr create --base <default> --head issue-<n>`, with:
   - **title**: the issue's title;
   - **body**: `Closes #<n>` plus the list of commits on `issue-<n>`
     not in the default branch (`gh api repos/<repo>/compare/<base>...issue-<n>`),
     one line each (short SHA + subject).
4. Post the result (PR URL) as an issue comment; if any step failed,
   the comment says so and links the run instead.

The `merge` messages are fixed English text (no agent to adapt them to
the issue's language).

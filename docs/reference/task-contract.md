---
id: task-contract
title: Task Contract
description: >
  Reference for the stable mise run task contract exposed by harness-scaffold
  projects, including both the fast engineering loop and the deterministic
  slice-handoff checks.
index:
  - id: contract-tasks
    keywords: [tasks, contract, stable, list, reference, plan]
  - id: check
    keywords: [check, quality-gate, fast, fmt-lint-typecheck-test]
  - id: verify
    keywords: [verify, heavy, integration, docker, slow]
  - id: ci
    keywords: [ci, entrypoint, github-actions]
  - id: slice-plan
    keywords: [slice-plan, slice-implement, slice-review, slice-status, prompts]
---

# Task Contract

Every project initialized from harness-scaffold exposes these tasks. The contract is **stable** — same command names regardless of stack or shape.

```bash
mise run <task>
```

## Contract tasks

| Task | Purpose | Speed |
|------|---------|-------|
| [`init`](#init) | Transform scaffold into a project | One-time |
| [`setup`](#setup) | Install deps, prepare environment | Fast |
| [`fmt`](#fmt) | Auto-format code | Fast |
| [`lint`](#lint) | Non-modifying lint checks | Fast |
| [`typecheck`](#typecheck) | Static type analysis | Fast |
| [`test`](#test) | Unit tests | Fast |
| [`build`](#build) | Produce artifacts | Medium |
| [`check`](#check) | fmt-check + lint + typecheck + test | Fast |
| [`plan-check`](#plan-check) | Validate active slice metadata and required files | Fast |
| [`spec-check`](#spec-check) | Validate decision promotion and reflected docs | Fast |
| [`evidence-check`](#evidence-check) | Validate declared evidence and artifact paths | Fast |
| [`review-check`](#review-check) | Validate external review artifacts | Fast |
| [`sync-check`](#sync-check) | Aggregate active or changed-plan handoff checks | Fast |
| [`slice-plan`](#slice-plan) | Render planner prompt for the active slice | Fast |
| [`slice-implement`](#slice-implement) | Render implementer prompt for the active slice | Fast |
| [`slice-review`](#slice-review) | Render reviewer prompt for the active slice | Fast |
| [`slice-status`](#slice-status) | Show active slice status | Fast |
| [`dev`](#dev) | Start local development | Long-running |
| [`ci`](#ci) | CI entrypoint (= check) | Fast |
| [`docs`](#docs) | Documentation server | Long-running |
| [`plan`](#plan) | Create a plan directory | Fast |
| [`verify`](#verify) | Heavy validation | Slow |

---

## init

Transforms the scaffold into your project. Run once after cloning.

```bash
mise run init                                      # interactive
mise run init -- --non-interactive --name myapp    # scripted
```

See [Getting Started](../how-to/getting-started.md) and [Init System](../explanation/init-system.md).

---

## setup

Installs all project dependencies. Safe to re-run.

=== "Python"
    ```bash
    uv sync --all-extras
    ```

=== "Go"
    ```bash
    go mod download
    ```

=== "Rust"
    ```bash
    cargo fetch
    ```

=== "Web"
    ```bash
    npm install --package-lock=false
    ```

For the apps workspace shape, `setup` iterates `workspace.toml` and runs the appropriate install per module.

---

## fmt

Auto-formats code in-place. Pass `--check` to fail without modifying (used by `check`).

=== "Python"
    ```bash
    uv run ruff format .          # format
    uv run ruff format --check .  # check only
    ```

=== "Go"
    ```bash
    gofumpt -w .   # format
    gofumpt -l .   # check only
    ```

=== "Rust"
    ```bash
    cargo fmt          # format
    cargo fmt --check  # check only
    ```

=== "Web"
    ```bash
    npm run fmt        # format
    npm run fmt:check  # check only
    ```

```bash
mise run fmt           # format in-place
mise run fmt --check   # check only (used by CI)
```

---

## lint

Non-modifying lint checks. Fails on any violation.

=== "Python"
    ```bash
    uv run ruff check .
    ```

=== "Go"
    ```bash
    golangci-lint run ./...
    ```

=== "Rust"
    ```bash
    cargo clippy --all-targets --all-features -- -D warnings
    ```

=== "Web"
    ```bash
    npm run lint
    ```

---

## typecheck

Static type analysis.

=== "Python"
    ```bash
    uv run ty check
    ```

=== "Go"
    ```bash
    go vet ./...
    ```

=== "Rust"
    ```bash
    cargo check --all-targets --all-features
    ```

=== "Web"
    ```bash
    npm run typecheck
    ```

!!! note "Go typecheck"
    Go's type system is enforced at compile time. `go vet` provides the closest equivalent to a standalone type-check pass.

---

## test

Unit tests only — no integration tests, no external services.

=== "Python"
    ```bash
    uv run pytest
    ```

=== "Go"
    ```bash
    CGO_ENABLED=0 go test ./...
    ```

=== "Rust"
    ```bash
    cargo test --all-features
    ```

=== "Web"
    ```bash
    npm run test
    ```

---

## Visual stacks

Blender projects use `mise run build` for a Blender background render and require Blender on `PATH` or `BLENDER_BIN`; `mise run verify` reopens the saved blend. Three.js projects use locked npm dependencies, native Node unit tests, and `mise run verify` for build plus optional local Playwright Chromium browser coverage. Both visual starters are single-project only.

## build

Produces distributable artifacts.

=== "Python"
    ```bash
    uv build
    ```

=== "Go"
    ```bash
    CGO_ENABLED=0 go build -o bin/ ./cmd/...
    ```

=== "Rust"
    ```bash
    cargo build --release
    ```

=== "Web"
    ```bash
    npm run build
    ```

---

## check

**The primary quality gate.** Runs fmt (check mode), lint, typecheck, and test sequentially. Fails fast on the first error.

```bash
mise run check
```

This is what you run before every commit and what CI runs. It must be:

- **Fast** — deterministic, no network, no external services
- **Non-interactive** — safe in CI and pre-commit hooks
- **Comprehensive** — catches formatting, lint, type, and test failures

---

## plan-check

Validates that the active slice has a current plan and required slice-local files.
When called with `--plan-dir`, validates that specific plan even if it is
already complete.

```bash
mise run plan-check
mise run plan-check -- --plan-dir .ai/plans/2026-04-29-134035-example
```

Checks for:

- one active in-progress plan at most
- required plan files
- valid `META.yaml` contract fields
- current checklist-style TODOs and learning-log coverage

---

## spec-check

Validates that durable contract and decision updates were promoted out of the
active plan, or a specific plan when called with `--plan-dir`.

```bash
mise run spec-check
mise run spec-check -- --plan-dir .ai/plans/2026-04-29-134035-example
```

Uses the active plan's `decision_record`:

- `none` → slice-local notes only
- `ledger` -> append to generated path docs/explanation/decision-ledger.md
- `adr` -> create or update a generated ADR under docs/explanation/decisions/

On the scaffold repo itself, the validator also accepts the legacy ADR location
under `docs/reference/decisions/`.

---

## evidence-check

Validates that declared evidence exists and points to real files.

```bash
mise run evidence-check
mise run evidence-check -- --plan-dir .ai/plans/2026-04-29-134035-example
```

Checks:

- `VALIDATION.md` contains explicit command records, not prose reminders
- every artifact path in artifacts/manifest.yaml exists
- every artifact path stays inside the active plan directory
- every artifact path is not ignored by git and is tracked or staged
- every `evidence_required` type in `META.yaml` is satisfied
- small committed evidence summaries are preferred over raw scratch artifacts

---

## review-check

Validates that the active slice has an external-enough review artifact, or a
specific plan when called with `--plan-dir`.

```bash
mise run review-check
mise run review-check -- --plan-dir .ai/plans/2026-04-29-134035-example
```

Checks:

- `REVIEW.md` exists and is not placeholder-only
- the recorded review mode is external when required
- the recorded backend is not self-review
- the recorded reviewer is not placeholder text
- the required rubrics were applied

---

## sync-check

Aggregates the non-code handoff checks.

```bash
mise run sync-check
mise run sync-check -- --plan-dir .ai/plans/2026-04-29-134035-example
mise run sync-check -- --changed-plans origin/main...HEAD
```

Default local mode runs:

1. `mise run plan-check`
2. `mise run spec-check`
3. `mise run evidence-check`
4. `mise run review-check`

`--plan-dir` runs those same checks against one explicit plan directory,
including completed plans. `--changed-plans` is intended for PR CI: it finds
changed `.ai/plans/<timestamp>-<slug>/` directories in the supplied git diff,
requires each changed plan to be `status: complete`, and validates each one. If
meaningful branch changes exist without a changed plan, the PR-mode check fails.

### Implementation Boundary

The task wrappers stay in `.mise/tasks/` because those files are the stable
agent-facing interface. The implementation for planning, prompt rendering,
status, and deterministic slice checks lives inside the `slice-workflow` skill:

- scaffold source: `templates/.agent/skills/slice-workflow/cli`
- generated repos: `.agent/skills/slice-workflow/cli`

The skill-local CLI is a small uv project with a `slice-workflow` console
command. Its package is `slice_workflow_cli`:

- `plan.py` — plan directory creation from repo templates
- `workflow.py` — prompt rendering and slice status output
- `checks.py` — `plan-check`, `spec-check`, `evidence-check`, `review-check`,
  and `sync-check` orchestration
- `templates/.agent/skills/slice-workflow/cli/src/slice_workflow_cli/contract/plans.py` — plan discovery, metadata validation, changed-plan
  selection
- `templates/.agent/skills/slice-workflow/cli/src/slice_workflow_cli/contract/git.py` — changed paths, branch names, ignored-path and tracked-path
  checks
- `templates/.agent/skills/slice-workflow/cli/src/slice_workflow_cli/contract/markdown.py` — frontmatter stripping, section parsing, placeholder
  checks
- `templates/.agent/skills/slice-workflow/cli/src/slice_workflow_cli/contract/artifacts.py` — manifest parsing and validation evidence detection
- `templates/.agent/skills/slice-workflow/cli/src/slice_workflow_cli/contract/docs.py` — repo path safety and decision-record lookup

The wrappers delegate to that CLI instead of importing repo-local helper
scripts. This keeps the workflow capability with the skill while preserving the
stable `mise run ...` interface.

---

## slice-plan

Renders the planner prompt for the active slice. The task snapshots the incoming
task into `TASK.md` and writes the rendered prompt to prompts/planner.md in the
active plan.

```bash
mise run slice-plan -- --task path/to/task.md
mise run slice-plan -- --task-text "Add --dry-run to the init command"
```

This task does not launch an agent. Paste the rendered prompt into the Codex,
Claude, or other harness session you already have open.

---

## slice-implement

Renders the implementer prompt for the active slice.

```bash
mise run slice-implement
```

Writes prompts/implementer.md using the current plan files as context.

---

## slice-review

Renders the reviewer prompt for the active slice.

```bash
mise run slice-review
```

Writes prompts/reviewer.md and points the reviewer at the plan, validation
log, durable decision notes, and configured rubrics.

---

## slice-status

Shows active slice state in human-readable text or JSON.

```bash
mise run slice-status
mise -q run slice-status -- --json
```

The JSON mode is intended for agents, CI experiments, and wrapper scripts.

---

## dev

Starts local development. Long-running — stays in the foreground.

=== "Python"
    ```bash
    uv run python -m <module>   # requires __main__.py
    ```

=== "Go"
    ```bash
    go run ./cmd/...
    ```

=== "Rust"
    ```bash
    cargo run
    ```

=== "Web"
    ```bash
    npm run dev
    ```

For the apps workspace shape:
```bash
mise run dev -- api      # start the 'api' module
```

---

## ci

CI entrypoint. Currently an alias for `check`.

```bash
mise run ci
```

GitHub Actions calls exactly this — nothing else. All quality gate logic lives in `check` which `ci` delegates to.

---

## docs

Starts the MkDocs documentation server locally.

```bash
mise run docs    # serves at http://127.0.0.1:8000
```

---

## plan

Creates a plan directory for a new unit of work. Scaffolds META.yaml, TODO.md,
LEARNING_LOG.md, VALIDATION.md, REVIEW.md, DECISIONS.md,
artifacts/manifest.yaml, and optional SPEC.md / IMPLEMENTATION.md.

```bash
git checkout -b feat/<slug>
mise run plan -- <slug>    # e.g., mise run plan -- add-user-auth
```

Creates `.ai/plans/YYYY-MM-DD-HHmmSS-<slug>/` with templates auto-filled (date,
branch). Refuses to run on the default branch. Slugs must be lowercase kebab-case
and unique within `.ai/plans/`.

In generated repos, see .ai/plans/AGENTS.md for the plan lifecycle. In this
scaffold repo, see `templates/.ai/plans/AGENTS.md` and
`templates/.ai/plans/_example/`.

---

## verify

Heavy validation that is **too slow for `check`**. Run before releases or on dedicated CI jobs.

Phases:

1. **check** — runs the full quality gate first
2. **Integration tests** — if the generated project has integration tests
3. **Docker build** — if `Dockerfile` exists

Rust generated projects rerun `cargo test --all-features` during `verify`, then
run the Docker build when a Dockerfile is present.

Web generated projects run `npm run build` and `npm run deploy:dry-run` after
the fast quality gate.

```bash
mise run verify
```

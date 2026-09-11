---
id: ci-hooks
title: CI & Hooks
description: >
  GitHub Actions workflow and pre-commit hook configuration. CI calls mise task
  entrypoints; hooks call the same tasks for guaranteed local parity.
index:
  - id: github-actions
    keywords: [workflow, ci-yml, mise-action, push, pull-request, two-tier]
  - id: pre-commit-hooks
    keywords: [pre-commit, hooks, fmt, lint, typecheck, test, install]
  - id: design-rationale
    keywords: [parity, always-run, single-source, logic-in-ci]
---

# CI & Hooks

## GitHub Actions

The CI workflow is intentionally thin: GitHub Actions installs tools and then
delegates validation to mise task entrypoints.

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  check:
    name: Quality Gate
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install mise
        uses: jdx/mise-action@v2
      - name: Setup
        run: mise run setup
      - name: Check
        run: mise run ci

  verify:
    name: Full Validation
    runs-on: ubuntu-latest
    needs: [check]
    if: github.event_name == 'pull_request'
    steps:
      - uses: actions/checkout@v4
      - name: Install mise
        uses: jdx/mise-action@v2
      - name: Setup
        run: mise run setup
      - name: Verify stack behavior
        run: mise run verify
```

`mise-action` installs mise and runs `mise install` automatically, pulling tool versions from `.mise.toml`.

Quality gate logic lives in `mise run ci` → `mise run check`. Generated pull
request CI also runs plain `mise run verify`, which retains the full quality gate
and stack-specific checks without guessing which custom product journeys apply.
Agents and engineers inspect named routes and run relevant ones explicitly during
implementation and closeout. The Harness Toolkit source repository separately
runs generated-project smoke tests across the standard stacks so Python, Go,
Rust, and Web scaffolds prove they can initialize and pass `mise run check`.

## Pre-commit hooks

Pre-commit hooks mirror CI exactly — every hook calls a `mise run` task:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: fmt
        entry: mise run fmt
        language: system
        always_run: true
        pass_filenames: false

      - id: lint
        entry: mise run lint
        # ...

      - id: typecheck
        entry: mise run typecheck
        # ...

      - id: test
        entry: mise run test
        # ...
```

This keeps **CI parity** for the fast quality gate: if pre-commit passes, the
`check` job should pass. The heavier pull-request job then runs stack-specific
verification. Custom product routes remain an explicit, evidence-backed choice.

### Installing hooks

```bash
mise run setup   # installs hooks automatically if pre-commit is available
# or manually:
pre-commit install
```

### Running hooks manually

```bash
pre-commit run --all-files   # run all hooks on all files
pre-commit run fmt           # run a specific hook
```

## Design rationale

**Why keep CI YAML thin?** GitHub Actions chooses the CI context, such as
whether a run is a pull request or a main-branch push. The validation logic
still lives in mise tasks: CI calls `mise run ci` and plain `mise run verify`,
while pre-commit calls `mise run <task>`. Named product routes can be added to a
project's closeout policy when that policy has an actual consumer and owner.

**Why `always_run: true`?** The tasks (`ruff`, `ty`, `pytest`) are fast enough that running them unconditionally is cheaper than filtering by changed files. It also prevents edge cases where a change to a config file doesn't trigger re-checking source files.

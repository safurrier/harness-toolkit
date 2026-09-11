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

  sync-check:
    name: Sync Contract
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Install mise
        uses: jdx/mise-action@v2
      - name: Setup
        run: mise run setup
      - name: Sync check
        run: |
          if [ "${{ github.event_name }}" = "pull_request" ]; then
            HK export integrity check -- --changed-from "origin/${{ github.base_ref }}...HEAD"
          else
            HK export integrity check
          fi
```

`mise-action` installs mise and runs `mise install` automatically, pulling tool versions from `.mise.toml`.

Quality gate logic lives in `mise run ci` → `mise run check`. Handoff export
integrity is checked with `mise run sync-check` when committed HK exports are
present. Pull request CI runs `mise run verify -- --changed-from
origin/<base>...HEAD` in generated projects, which selects required product
routes for the changed paths while retaining the full quality gate. The repository
CI also runs generated-project smoke tests across the supported stacks so Python,
Go, Rust, and Web scaffolds prove they can initialize and pass `mise run check`.

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

This guarantees **CI parity** for the fast quality gate: if pre-commit passes,
the `check` job should pass. `sync-check` remains the explicit handoff gate for
slice evidence and review completeness, with PR CI using changed-plan mode.

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
still lives in mise tasks: CI calls `mise run ci`, HK export integrity check, or
`HK export integrity check -- --changed-from ...`, and pre-commit calls
`mise run <task>`.

**Why `always_run: true`?** The tasks (`ruff`, `ty`, `pytest`) are fast enough that running them unconditionally is cheaper than filtering by changed files. It also prevents edge cases where a change to a config file doesn't trigger re-checking source files.

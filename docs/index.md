---
id: harness-toolkit-overview
title: harness-toolkit
description: >
  Overview of the Harness Engineering Toolkit: Harness Kit for existing repos
  and harness-scaffold for new repos.
index:
  - id: choose-your-path
    keywords: [scaffold, clone-and-init, task-contract, agent-native]
  - id: why-mise
    keywords: [mise, tool-versions, task-runner, unified]
  - id: quick-start
    keywords: [install, clone, init, setup]
  - id: supported-stacks
    keywords: [python, go, rust, web, stacks, status]
---

# harness-toolkit

**Harness Engineering Toolkit** for agent-ready repositories.

Use **`hk` / `harness-kit`** for portable planning, validation, and handoff workflow in existing repos. Use **`harness-scaffold`** to start a new repo with the workflow, docs, CI, and stack defaults already wired in.

For the product philosophy behind HK's lifecycle, config, and readiness model, see [Harness Kit: Dumb Tasks, Smart Agents](explanation/harness-kit-what-and-why.md).

## Choose your path

| Starting point | Use | First command |
| --- | --- | --- |
| An existing repository | `hk` / `harness-kit` for optional lifecycle evidence and handoff | `hk --version` |
| A new repository | `harness-scaffold` for docs, CI, and native task defaults | `harness-scaffold init` |

`hk` does not replace the repository's commands. `harness-scaffold` creates a
new repository contract; it does not require an HK ledger in CI.

## Why mise

[mise](https://mise.jdx.dev/) manages both **tool versions** (Python, Go, uv, gofumpt, golangci-lint) and **task wrappers** through one managed command surface. It replaces Makefiles, shell scripts, and per-language task runners with a unified interface that works the same locally and in CI.

## Quick start

Install the CLIs for portable use in existing repos:

```bash
uv tool install git+https://github.com/safurrier/harness-toolkit.git
hk --version
```

Initialize a new repo from the scaffold:

```bash
# 1. Install mise (only prerequisite)
curl https://mise.run | sh

# 2. Clone
git clone https://github.com/safurrier/harness-toolkit.git my-project
cd my-project

# 3. Install tools
mise install

# 4. Initialize
mise run init
```

See [Getting Started](how-to/getting-started.md) for the full walkthrough and
[Release and Installation](how-to/release.md) for uv tool installs and tag releases.

## Supported stacks

| Stack  | Format         | Lint           | Typecheck   | Test       | Status      |
|--------|----------------|----------------|-------------|------------|-------------|
| Python | ruff format    | ruff check     | ty          | pytest     | ✅ Available |
| Go     | gofumpt        | golangci-lint  | go vet      | go test    | ✅ Available |
| Rust   | cargo fmt      | cargo clippy   | cargo check | cargo test | ✅ Available |
| Web    | prettier       | eslint         | tsc         | vitest     | ✅ Available |

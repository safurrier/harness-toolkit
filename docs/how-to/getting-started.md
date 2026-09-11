---
id: getting-started
title: Getting Started
description: >
  Step-by-step guide to installing mise, cloning harness-toolkit, and running
  mise run init to initialize a new project interactively or non-interactively.
index:
  - id: prerequisites
    keywords: [mise, install, homebrew, curl, winget, path]
  - id: initialize-a-project
    keywords: [init, interactive, non-interactive, name, shape, stack]
  - id: after-init
    keywords: [setup, check, dev, next-steps]
---

# Getting Started

## Prerequisites

Only **mise** needs to be on your `PATH`. It manages everything else.

=== "macOS / Linux (curl)"
    ```bash
    curl https://mise.run | sh
    ```

=== "macOS (Homebrew)"
    ```bash
    brew install mise
    ```

=== "Windows (PowerShell)"
    ```powershell
    winget install jdx.mise
    ```

Once mise is installed, `mise install` pulls down all tools declared in `.mise.toml` — currently Python and uv for the scaffold itself, then stack-specific tooling after `init`.

## Install the CLIs for existing repos

If you want to use `hk` / `harness-kit` from any repository, install Harness
Toolkit as a uv tool:

```bash
uv tool install git+https://github.com/safurrier/harness-toolkit.git
```

For a pinned release tag:

```bash
uv tool install git+https://github.com/safurrier/harness-toolkit.git@v0.3.0
```

For local development from a checkout:

```bash
uv tool install --editable ~/git_repositories/harness-toolkit
```

Verify:

```bash
hk --version
harness-kit --version
harness-scaffold --version
```

Use `hk` for portable planning in existing repos. Use `harness-scaffold` when
initializing a new repo from the template.

## Initialize a project

### Interactive

```bash
git clone https://github.com/safurrier/harness-toolkit.git my-project
cd my-project
mise install
mise run init
```

The interactive flow prompts for:

1. **Project name** — lowercase, hyphens allowed (e.g. `my-service`)
2. **Description** — one-line project description
3. **Shape** — `single` (one language) or `apps` (workspace with multiple apps)
4. **Stack** — `python`, `go`, `rust`, `web`, `blender`, or `threejs`
5. **Author** name and email
6. **Options** — pre-commit hooks, example code

### Non-interactive

```bash
mise run init -- \
  --non-interactive \
  --name my-service \
  --shape single \
  --stack python
```

Full flag reference:

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--name` | Yes | — | Project name (lowercase, hyphens) |
| `--description` | No | `A <name> project` | One-line description |
| `--shape` | No | `single` | `single` or `apps` |
| `--stack` | No | `python` | `python`, `go`, `rust`, `web`, `blender`, or `threejs` |
| `--modules` | For apps | — | Comma-separated module names |
| `--go-module` | For Go | `github.com/your-org/<name>` | Go module path |
| `--web-ui` | For Web | `plain` | Web UI variant: `plain`, `tailwind`, or `shadcn` |
| `--web-db` | For Web | `d1` | Cloudflare D1 access layer: `d1` or `drizzle-d1` |
| `--author-name` | No | — | Author name |
| `--author-email` | No | — | Author email |
| `--no-hooks` | No | hooks enabled | Skip pre-commit installation |
| `--no-examples` | No | examples kept | Remove example source files |

For a Cloudflare-ready web app:

```bash
mise run init -- \
  --non-interactive \
  --name my-dashboard \
  --shape single \
  --stack web
```

For the more opinionated app starter with Tailwind, shadcn/ui, and Drizzle over
Cloudflare D1:

```bash
mise run init -- \
  --non-interactive \
  --name my-dashboard \
  --shape single \
  --stack web \
  --web-ui shadcn \
  --web-db drizzle-d1
```

## After init

```bash
mise run setup   # install dependencies
mise run check   # verify everything passes
mise run dev     # start developing
```

!!! tip "What init does"
    See [Init System](../explanation/init-system.md) for a detailed walkthrough of everything `mise run init` does to transform the scaffold into your project.

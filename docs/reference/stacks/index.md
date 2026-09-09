---
id: stacks-overview
title: Stacks
description: >
  Overview of supported language and visual stacks (Python, Go, Rust, Web, Blender, Three.js), with a
  per-stack tool comparison table and how to select a stack at init time.
index:
  - id: stack-comparison
    keywords: [python, go, rust, web, fmt, lint, typecheck, test, comparison]
  - id: stack-selection
    keywords: [select, init, scaffold-project-stack, env-var]
  - id: detailed-docs
    keywords: [acceptance, rubric, future-stack, checklist]
---

# Stacks

A **stack** is the set of language-native tools wired into the task contract. Every task delegates to its stack's tools.

## Stack comparison

| | Python | Go | Rust | Web (TS) |
|--|--------|-----|------|----------|
| **Status** | ✅ Available | ✅ Available | ✅ Available | ✅ Available |
| **fmt** | ruff format | gofumpt | cargo fmt | prettier |
| **lint** | ruff check | golangci-lint | cargo clippy | eslint |
| **typecheck** | ty | go vet | cargo check | tsc --noEmit |
| **test** | pytest | go test | cargo test | vitest |
| **build** | uv build | go build | cargo build --release | vite build |
| **deploy check** | Package build | Docker build | Docker build | wrangler deploy dry-run |
| **Tool manager** | uv | go toolchain | cargo | npm |

| | Blender | Three.js |
|--|---------|----------|
| **Status** | ✅ Available (local Blender required to render) | ✅ Available |
| **fmt** | ruff format | prettier |
| **lint** | ruff check | eslint |
| **typecheck** | ty | tsc --noEmit |
| **test** | pytest source checks | node --test |
| **build** | Blender render | vite build |
| **verify** | render + reopen | build + Playwright E2E |
| **Tool manager** | uv + Blender | npm |

## Stack selection

Set at `init` time via `--stack`:

```bash
mise run init -- --non-interactive --name myapp --shape single --stack python
mise run init -- --non-interactive --name myservice --shape single --stack go
mise run init -- --non-interactive --name mydaemon --shape single --stack rust
mise run init -- --non-interactive --name mydashboard --shape single --stack web
mise run init -- --non-interactive --name mydashboard --shape single --stack web --web-ui shadcn --web-db drizzle-d1
mise run init -- --non-interactive --name garden-scene --shape single --stack blender
mise run init -- --non-interactive --name visual-game --shape single --stack threejs
```

Web stack variants are opt-in. `--web-ui` accepts `plain`, `tailwind`, or
`shadcn`; `--web-db` accepts `d1` or `drizzle-d1`.

After init, the stack is recorded in `.mise.toml`:

```toml
[env]
SCAFFOLD_PROJECT_STACK = "python"
```

All task scripts read this variable to dispatch to the correct toolchain.

## Detailed docs

- [Stack acceptance rubric](acceptance-rubric.md)
- [Python stack](python.md)
- [Go stack](go.md)
- [Rust stack](rust.md)
- [Web stack](web.md)
- [Web app template summary](web-template-summary.md)
- [Visual stacks](visual.md)

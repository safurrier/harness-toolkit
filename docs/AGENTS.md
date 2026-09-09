# docs/ Index

Agent routing index for MkDocs-managed documentation. Structure is owned by `mkdocs.yml` and follows an intent-based layout: `explanation/`, `how-to/`, and `reference/`.

## Explanation

| Doc | Description |
|-----|-------------|
| `index.md` | Project overview, design philosophy, quick start |
| `explanation/harness-kit-what-and-why.md` | Product philosophy for HK: deterministic checks and explicit context make tasks dumb so agents can be smart |
| `explanation/portable-workflow.md` | Attaching the planning workflow to existing repos without committed scaffold files |
| `explanation/harness-kit-lifecycle-design.md` | Lifecycle-first local assistant design backed by ledger state |
| `explanation/system-map-mental-model.md` | How system maps complement profiles by adding component and invariant context to changed paths |
| `explanation/shapes.md` | Single-project vs apps workspace: layouts, workspace.toml, task behavior |
| `explanation/init-system.md` | How init transforms the scaffold: sequence, templates, cleanup |
| `explanation/ci.md` | CI workflow design: mise entrypoints, sync contract, pre-commit parity |
| `explanation/script-contract-prototype.md` | Prototype for thin `scripts/*` adapter contract as a future scaffold task surface |

## How-to

| Doc | Description |
|-----|-------------|
| `how-to/getting-started.md` | Install mise, clone, init a project interactively or non-interactively |
| `how-to/agent-adoption.md` | Add Harness Kit to user-level AGENTS.md and guide agents that are unfamiliar with `hk` |
| `how-to/profile-reviews.md` | HK profile reviews, suggested/required review policies, and skill-backed review instructions |
| `how-to/profile-authoring.md` | HK profile authoring guidance for focused iteration, final gates, targeted follow-up, and avoiding closeout loops |
| `how-to/system-map-authoring.md` | `.harness/system.toml` authoring guidance for components, must-preserve invariants, and profile check-label integration |
| `how-to/development.md` | Contribute to the scaffold: test layers, fixtures, adding stacks |
| `how-to/release.md` | uv tool installation, GitHub tag release checklist, PyPI deferral |

## Reference

| Doc | Description |
|-----|-------------|
| `reference/task-contract.md` | Stable mise task contract, per-stack commands, speed tier |
| `reference/stacks/index.md` | Stack comparison table, selection at init time |
| `reference/stacks/acceptance-rubric.md` | Future stack acceptance bar and reviewer checklist |
| `reference/stacks/python.md` | Python tooling: uv, ruff, ty, pytest configuration |
| `reference/stacks/go.md` | Go tooling: gofumpt, golangci-lint, go test, Dockerfile |
| `reference/stacks/rust.md` | Rust tooling: cargo fmt, clippy, check, test, Dockerfile |
| `reference/stacks/web.md` | Web tooling and optional variants: Vite, React, Tailwind/shadcn, Cloudflare Workers, D1/Drizzle, Prettier, ESLint, Vitest |
| `reference/stacks/visual.md` | Blender and Three.js visual starter tooling, edit seams, and local prerequisites |
| `reference/decisions/0001-spec-driven-decision-loop.md` | SPEC.md, docs, and ADR loop |
| `reference/decisions/0002-plan-workflow.md` | Plan directory workflow |
| `reference/decisions/0003-deterministic-slice-contract.md` | Plan/spec/evidence/review contract |
| `reference/decisions/0004-skill-first-slice-workflow.md` | Skill-first slice workflow |
| `reference/decisions/0005-harden-sync-contract-ci.md` | Changed-plan sync-check CI mode |
| `reference/decisions/0006-followup-contract-stack-rubric.md` | Slice workflow CLI and stack rubric |
| `reference/decisions/0007-harness-toolkit-naming.md` | Harness Engineering Toolkit naming split: `hk`, `harness-kit`, `harness-scaffold` |
| `reference/decisions/0008-harness-kit-ledger-first-local-assistant.md` | Initial lifecycle decision: local ledger, sync checkpoints, evidence capture |
| `reference/decisions/0009-harness-kit-lifecycle-first-cli.md` | Lifecycle-first CLI decision that preserves handoff-safety guarantees |
| `reference/decisions/0010-compact-hk-export-packages.md` | Compact `.ai/hk` export package shape and ledger/projection boundary |
| `reference/decisions/0011-path-aware-review-freshness.md` | Path/content-aware HK review freshness and targeted follow-up review coverage |
| `reference/decisions/0012-lifecycle-neutral-active-hk-exports.md` | Lifecycle-neutral active HK handoff exports and strict export integrity checks |
| `reference/decisions/0013-web-stack-v0.md` | Web stack V0: Vite/React, optional Tailwind/shadcn, Cloudflare Workers, D1/Drizzle persistence scaffold |

<!-- generated-by: context-engineering@2.2.0 | last-updated: 2026-06-02 -->

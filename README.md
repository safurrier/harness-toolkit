# harness-toolkit

Harness Toolkit is a monorepo for two related but separate tools built around one idea: **dumb tasks, smart agents**. Deterministic checks and explicit context make the task surface boring so the agent can spend its judgment on the actual work.

- **`hk` / `harness-kit`** — a lifecycle and readiness CLI for existing
  repositories. It records plan, context, validation evidence, review, sync
  state, and handoff output without forcing scaffold files into the repo.
- **`harness-scaffold`** — a project generator for new agent-ready repositories.
  It creates a stable `mise` task contract, docs structure, CI wiring, and
  explicitly selected product-verification routes.

Use `hk` when the repository already exists and you want safer agent handoff.
Use `harness-scaffold` when you are starting a new repository and want the
workflow installed from day one. They share a release/package because they share
the same philosophy, but they solve different jobs.

## Install

Harness Toolkit is currently distributed as a GitHub-sourced Python tool. PyPI is
intentionally deferred until the CLI contracts settle; prefer explicit GitHub
`main` or tag installs.

```bash
uv tool install git+https://github.com/safurrier/harness-toolkit.git
```

For a pinned release:

```bash
uv tool install git+https://github.com/safurrier/harness-toolkit.git@v0.3.0
```

For local development from a checkout:

```bash
uv tool install --editable ~/git_repositories/harness-toolkit
```

Verify both apps are installed:

```bash
hk --version
harness-kit --version
harness-scaffold --version
```

See [Release and Installation](docs/how-to/release.md) for upgrade commands, release
checklists, and the current no-PyPI-yet policy. The published docs site lives at
<https://safurrier.github.io/harness-toolkit/>.

## App 1: `hk` for existing repositories

`hk` is for meaningful agent-driven changes: broad edits, risky work,
multi-step changes, or anything that may need context compaction or human
handoff. It is not a replacement task runner; keep running the repo's native
commands and let `hk` record what happened.

```bash
cd existing-repo
hk profile resolve --target . --json   # optional discovery
hk start demo-work --plan "Adopted implementation intent" --target .
# edit normally and run repo-native commands
hk checks --target . --changed --json   # suggests checks/reviews, does not run them
hk validate --why "Fast gate passes" --target . -- mise run check
hk status --target .
hk ready --target .
hk summary --target .
```

`hk status` is the coach. Agents should follow its next actions instead of
memorizing a long checklist. It will ask for missing context, plan updates,
decision/spec reflection, validation evidence, external-enough review, sync, or
an explicit dangerous skip when a lifecycle guarantee cannot be met.

To make this the default behavior for agents, add the compact directive from
[Agent Adoption](docs/how-to/agent-adoption.md) to your user-level or repo-level
`AGENTS.md`.

### `hk` lifecycle model

`hk` preserves a simple handoff-safety spine:

```text
plan → decision/spec reflection → validation evidence → external-enough review → readiness gate → handoff artifact
```

The readiness ledger is local state first. `hk` can render summaries, handoffs,
and exported packages, but it does not require existing repos to commit generated
ceremony.

`hk status` is the coach. It tells the agent when to add optional context, record
a decision/spec reflection, dispatch review, reconcile sync state, or use a
scary explicit bypass. Agents should not memorize a long command checklist.
User-level `harness.toml` can bind known repo/module paths to inline profiles or
to standalone TOML profiles loaded from `profiles_dir`, so agents do not need
validation/review conventions re-explained every session. Target bindings can
also attach a `system_map` file from user config/dots for personal overlays on
shared repos; paths inside that map stay repo-root-relative. If an agent works in
a Git linked worktree, HK projects configured repo/module target bindings from
the canonical worktree into the linked worktree before falling back to the
default profile. Separate clones are not auto-matched by remote URL. Profiles can
suggest checks/reviews for changed paths and mark specific path matches as
required while still leaving execution and reviewer dispatch to the agent. Path
rules accept both repo-root-relative changed paths and target-relative paths for
scoped module targets. `hk config inspect|validate|explain|audit` provides
read-only diagnostics for those bindings, profiles, and system maps; it explains
and validates deterministic config joins without generating config or running
profile commands.

Common `hk` actions:

| When you need to... | Use... |
|---|---|
| Start or inspect work | `hk start --plan ...`, `hk status`, `hk work status` |
| Inspect config/profile/system-map joins | `hk config inspect`, `hk config validate`, `hk config explain`, `hk config audit` |
| Record context, plan, or decisions | `hk context`, `hk plan`, `hk decide` |
| Capture command evidence | `hk validate --why "..." -- <native command>` |
| Add independent review | `hk review prompt`, then `hk review add` |
| Reconcile local state | `hk sync` or explicit `hk sync --exclude PATH --reason ...` |
| Check or share readiness | `hk ready`, `hk summary`, `hk handoff`, `hk export` |
| Make an explicit exception | `hk dangerously-skip review|validation|sync ...` |

Lower-level commands such as `hk note`, `hk evidence`, `hk capture`, and
`hk spec` are escape hatches, not the promoted path. See
[Harness Kit Design](docs/explanation/harness-kit-lifecycle-design.md),
[Profile Authoring](docs/how-to/profile-authoring.md), and
[Profile Reviews](docs/how-to/profile-reviews.md) for lifecycle and profile details.

## App 2: `harness-scaffold` for new repositories

`harness-scaffold` creates a new repo shape with the expected agent-facing task
contract already present. It is a generator, not the normal way to use `hk` in an
existing repository.

Only [mise](https://mise.jdx.dev/) needs to be on your `PATH`; it installs the
Python/uv tooling declared by the checkout and stack-specific tools after init.

```bash
# macOS / Linux
curl https://mise.run | sh

# or macOS with Homebrew
brew install mise
```

Then initialize an empty project directory:

```bash
mkdir my-project
cd my-project
harness-scaffold init
```

For non-interactive setup:

```bash
harness-scaffold init \
  --non-interactive \
  --name my-project \
  --shape single \
  --stack python
```

A source checkout also exposes `mise run init` as a development wrapper around
that same scaffold init path.

After init, use the generated repo's stable task contract:

```bash
mise run setup
mise run check
mise run dev
```

See [Getting Started](docs/how-to/getting-started.md), [Task Contract](docs/reference/task-contract.md),
[Repo Shapes](docs/explanation/shapes.md), and [Stacks](docs/reference/stacks/index.md) for the full
scaffold reference.

### Scaffolded task contract, stacks, and shapes

Every project initialized from `harness-scaffold` gets the same task names, with
thin `mise` orchestration delegating to language-native tools:

| Workflow | Tasks |
|---|---|
| Setup and local loop | `setup`, `fmt`, `lint`, `typecheck`, `test`, `build`, `check`, `dev` |
| CI and heavier validation | `ci` (= `check`), `verify` |
| Product verification | `verify` runs stack checks and selected executable routes |

Supported scaffold stacks:

| Stack | Format | Lint | Typecheck | Test | Status |
|---|---|---|---|---|---|
| Python | `ruff format` | `ruff check` | `ty` | `pytest` | Available |
| Go | `gofumpt` | `golangci-lint` | `go vet` | `go test` | Available |
| Rust | `cargo fmt` | `cargo clippy` | `cargo check` | `cargo test` | Available |
| Web / TypeScript | `prettier` | `eslint` | `tsc --noEmit` | `vitest` | Available |
| Blender | `ruff format` | `ruff check` | — | artifact checks | Available (single only) |
| Three.js | `prettier` | `eslint` | `tsc --noEmit` | browser E2E | Available (single only) |

The Web stack defaults to plain CSS plus raw Cloudflare D1 prepared statements.
Opt in to app-starter opinions with `--web-ui tailwind`, `--web-ui shadcn`, or
`--web-db drizzle-d1`.

Repo shapes are **single-project** and **apps workspace**. The full reference is
in [Task Contract](docs/reference/task-contract.md), [Stacks](docs/reference/stacks/index.md), and
[Repo Shapes](docs/explanation/shapes.md).

## Develop this checkout

This repository dogfoods `hk`, but normal development still starts with the
repo's own commands:

```bash
mise install
mise run setup
uv run pytest -m "not slow"   # focused iteration
mise run check                 # final fast gate
```

For meaningful Harness Toolkit changes, record the work with `hk`, validate with
repo-owned commands, get an external-enough review, then export a compact handoff
package when useful:

```bash
hk start demo-work --plan "Adopted implementation intent" --target .
hk validate --why "Fast gate passes" --target . -- mise run check
hk review prompt --target .
hk status --target .
hk ready --target .
```

Use `scripts/hk-dev ...` when you need to exercise this checkout's development
version of `hk` before the installed tool is updated.

## Design principles

1. **Two apps, one package** — `hk` serves existing repositories;
   `harness-scaffold` creates new ones. Do not make readers infer which surface
   they need.
2. **Stable command surface** — agents and humans can rely on the same names
   across stacks and repo shapes.
3. **Thin orchestration** — `mise` task wrappers delegate to native tools instead
   of hiding the shell.
4. **Fast local gate, explicit heavy gate** — `mise run check` is the default;
   `mise run verify` is reserved for slower validation.
5. **Readiness over ceremony** — `hk` records enough plan, evidence, review, and
   sync state to make handoff honest without making existing repos adopt scaffold
   files.
6. **Explicit exceptions** — skipped validation, review, or sync must be recorded
   with scary, intentional `dangerously-skip` commands and mitigations.

## More docs

- [Harness Kit: Dumb Tasks, Smart Agents](docs/explanation/harness-kit-what-and-why.md) — what and why behind HK's lifecycle, config, and readiness model
- [Harness Kit Design](docs/explanation/harness-kit-lifecycle-design.md) — lifecycle and ledger model
- [Agent Adoption](docs/how-to/agent-adoption.md) — small `AGENTS.md` directive for agents
- [Getting Started](docs/how-to/getting-started.md) — scaffold walkthrough
- [Task Contract](docs/reference/task-contract.md) — full generated task reference
- [Development Guide](docs/how-to/development.md) — working on this checkout
- [Release and Installation](docs/how-to/release.md) — install, upgrade, and release policy

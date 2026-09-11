---
id: portable-workflow
title: Portable Workflow
description: >
  Harness Kit CLI for attaching portable planning workflow state to an existing
  repository without committing scaffold files.
index:
  - id: overview
    keywords: [portable, attach, workflow, shared-repo, external, overlay]
  - id: harness-instruction-model
    keywords: [AGENTS.md, harness, instructions, minimal]
  - id: modes
    keywords: [external, overlay, git-info-exclude, local-state]
  - id: commands
    keywords: [hk, plan, status, sync-check, instructions]
---

# Portable Workflow
> **Historical note:** The generated slice-plan workflow described below was retired for new projects by [ADR 0014](../reference/decisions/0014-retire-slice-plans.md). Existing generated repositories remain legacy.


`hk` is the Harness Kit CLI for using portable planning and local-assistant
workflow state in a repository that was not initialized from harness-scaffold. It
is meant for shared codebases where committing `.ai/`, `.agent/`, `.mise/`,
`.harness/`, or `.gitignore` changes is not appropriate. The readable command is
`harness-kit`; the daily short command is `hk`.

Harness Kit is a lifecycle-first local assistant backed by ledger state:
read-only repo briefs, ignored/external work ledgers, typed learning/decision/gap
notes, sync checkpoints, captured command evidence, generated handoffs, and
optional local specs. See [Harness Kit Design](harness-kit-lifecycle-design.md).

The CLI uses Cyclopts so command signatures carry Python type information (for
example `Literal["external", "overlay"]` for mode choices) while still producing
focused help for agents.

## Install

Install `hk` from GitHub as a uv tool:

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

Verify:

```bash
hk --version
harness-kit --version
```

## Overview

Harness Kit keeps workflow state separate from target repository ownership:
`--target` identifies the repo or module that owns the work, while `--profile`
identifies the workflow/check contract to follow.

## Which workflow should I use?

Harness Kit exposes a lifecycle for agent work that needs local memory, exact
command evidence, review records, readiness checks, and a generated handoff
without committing ceremony:

```bash
hk brief --target . --json
hk start demo-work --plan 'Adopted implementation intent' --target . --json
hk validate --why 'Fast gate passes' --target . -- mise run check
hk status --target . --json
hk ready --target . --json
hk handoff --target . --format markdown
```

Portable plan-artifact commands were removed from `hk`: there is no `hk
attach`, `hk legacy plan`, or `hk legacy sync-check`. New scaffolded repositories
use native `mise run check` and `mise run verify`, with optional named
verification routes chosen explicitly from code and product context. Durable
guidance lives in `AGENTS.md` and `docs/`. Existing
generated repositories that retain plan packages are legacy.

Conceptually, the intended agent/human lifecycle is:

```text
research → plan → implement → validate → review → handoff
```

Planning can happen outside HK in chat, issues, or scratch docs. Once the plan is
stable enough to implement, agents should translate the agreed intent into a
compact HK plan note, for example:

```bash
hk plan --from-file /tmp/adopted-plan.md --target .
```

HK records the explicit plan; it does not parse conversations or infer plans.
Today, plan artifacts represent that lifecycle as Markdown/YAML files. Harness Kit's
target is to represent it as ledger events and generate the Markdown/YAML views
when needed.

## Harness instruction model

The intended adoption path is a tiny durable instruction in a user's global or
repo-level `AGENTS.md`, not a pile of committed scaffold files in every shared
repo. See [Agent Adoption](../how-to/agent-adoption.md) for the user-level snippet and
agent-facing first steps.

Print the user-level snippet with:

```bash
hk instructions
hk instructions --scope user --json
```

For repo-local adoption, `hk instructions --scope repo` prints a fuller
profile-specific snippet:

````markdown
## Portable agent workflow

Use `hk` for meaningful work in this repo or scoped path unless stronger repo-specific instructions supersede it. Treat Harness Kit and agent-generated local state as uncommitted unless the repo instructions or user explicitly say it should be committed.

Standard loop:

```bash
hk brief --target . --json
hk start demo-work --plan 'Adopted implementation intent' --target . --json
hk checks --target . --json
hk validate --why 'Fast gate passes' --target . -- mise run check
hk status --target . --json
hk ready --target . --json
hk handoff --target .
```

For monorepos, pass `--target` as the subdirectory that owns the lifecycle state.
HK stores local state under `.harness-local/`, ignored via `.git/info/exclude`.
````

## Local state

Harness Kit state is local to the target checkout by default. It lives under
`.harness-local/` and HK adds a local-only ignore rule to `.git/info/exclude`.
There is no external/overlay plan-artifact mode in `hk` anymore.

## Agent journey

`hk` is a readiness ledger for serious agent-driven changes. It is not trying
to be a human task manager or a native task runner. Humans usually add a small
`AGENTS.md` directive, shape the work in chat/issues/scratch docs, then hand the
agreed intent to an implementation agent and tell it to use `hk`. HK is most
useful when the change is broad, risky, multi-step, likely to span context
compaction, or when skipped validation needs to be explicit.

The minimal path is:

```bash
hk start demo-work --plan 'Adopted implementation intent'
hk validate --why 'Fast gate passes' -- mise run check
hk status
hk ready
hk summary
```

If an agent retries `hk start` with the same slug while that work item is still
active, HK resumes the active work item instead of creating duplicate retry
state. Use a new slug only when you intentionally want a separate work item.
`hk start --plan` is a convenient seed, not a requirement to predict every step
up front; agents can use repeated `hk plan "..."` notes as a living plan when
the implementation shape emerges progressively.

`hk status` is the journey guide. It tells the agent when to record context,
decisions/spec impact, review, sync, or explicit dangerous skips.

## User config and profiles

For cross-repo use, HK can load a user-level config from:

1. `$HARNESS_KIT_CONFIG`
2. `$XDG_CONFIG_HOME/harness-toolkit/harness.toml`
3. `~/.config/harness-toolkit/harness.toml`

The config is explicit routing plus inline or directory-backed profile guidance.
It does not auto-run checks and does not silently ignore sync paths.

```toml
version = 1
default_profile = "generic"
# Optional: load standalone profile TOML files relative to this config file.
profiles_dir = "profiles"

[[targets]]
name = "foreman"
path = "~/git_repositories/foreman"
profile = "foreman"
# Optional personal/user-level system map for shared repos or dots-managed overlays.
# Paths inside the map remain repo-root-relative.
system_map = "system-maps/foreman.toml"

[profiles.foreman]
title = "Foreman"
summary = "Rust CLI/TUI project."
target_hint = "~/git_repositories/foreman"
instructions = """
Use focused cargo tests while iterating.
Use `cargo fmt --check` before handoff.
For review, use Codex via `codex review --uncommitted` when available.
"""

[[profiles.foreman.checks]]
name = "cli-config-tests"
purpose = "Run CLI config tests."
command_template = "cargo test --test cli_config"
run_from = "repo-root"
applies_when = ["src/cli/**", "tests/cli/**"]
required_when = ["src/cli/**", "!src/cli/generated/**"]

[[profiles.foreman.reviews]]
name = "agent-friendly-cli-review"
purpose = "Review CLI changes against agent-facing CLI design principles."
backend = "fresh-context-subagent"
dispatch_hint = "Use a fresh-context reviewer."
applies_when = ["src/cli/**", "docs/**"]
required_when = ["src/cli/**", "!src/cli/generated/**"]

[profiles.foreman.reviews.instructions]
type = "file"
path = "prompts/agent-friendly-cli-review.md"
```

`applies_when` makes `hk checks --changed` and `hk status` suggest an item for matching changed
paths. `required_when` makes readiness expect that named check/review when the
path rule matches **when that profile is the target's resolved user-config
profile**. Profiles inspected with `--profile` / `--profiles-dir` are discovery
only unless they are also bound through user config. Agents satisfy required
checks with `hk validate --check fast-gate --why "Fast gate passes" -- mise run check` using the matching native command, and required
reviews with `hk review add --review NAME ...`. Later small deltas can use
`hk review add --review NAME --path REPO_RELATIVE_PATH ...` to record targeted
follow-up review for specific changed paths. If the required item is genuinely
impossible, record an auditable skip whose `--label` matches the check or review
name. `hk checks --changed --json` and `hk status --json` include matched repo-root paths and the
triggering path patterns so agents can explain why a check/review is required
without reverse-engineering the profile TOML. See [Profile Reviews](../how-to/profile-reviews.md)
for skill-backed review prompts and suggested vs required review patterns.

Path rules use gitignore-style patterns. Patterns are evaluated against the
repo-root-relative changed path and, when `--target` points at a subdirectory,
against the changed path relative to that target. This lets a module profile use
natural target-relative rules such as `cap/**` while still accepting explicit
repo-root rules such as `discord_cap/cap/**`. Matched paths in output remain
repo-root-relative so evidence and review prompts line up with Git.

Important examples:

- `*.md` matches Markdown files at any depth, including `docs/guide.md`.
- `/*.md` matches Markdown files only at the repo root.
- `docs/**` matches everything under `docs/`.
- `.github/**` is required for dot-directories; `github/**` does not match `.github/`.
- Later negated patterns can remove matches, e.g. `required_when = ["src/**", "!src/generated/**"]`.

Use:

```bash
hk profile resolve --target . --json   # includes direct/default/worktree match kind
hk checks --target . --changed --json  # includes matched files and triggering patterns
hk review prompt agent-friendly-cli-review --target .
```

Profile flags are discovery inputs, not lifecycle state. Use `--profile` and
`--profiles-dir` with commands that explicitly document them, such as
`hk checks`, `hk profile`, and repo-scope `hk instructions`; do not pass those
flags to lifecycle commands such as `hk start`, `hk validate`, `hk status`,
`hk ready`, or `hk handoff`.

Resolution uses explicit longest path-prefix matching first. If no configured
path matches and the target is in a Git linked worktree, HK compares Git common
directories and projects configured repo/module target bindings into the linked
worktree before applying the same longest-prefix rule. This lets ephemeral agent
worktrees inherit canonical repo profiles without adding temporary target entries.
Separate clones are not auto-matched by remote URL. If a profile has multiple
review entries, the agent should dispatch the applicable ones independently/in
parallel when the harness supports it, then record accepted reviews with
`hk review add --review NAME ...`.

Repo-level `.harness/harness.toml`, structured review backend adapters, and
persistent sync ignore config are deferred.

## Commands

| Command | Purpose |
|---|---|
| `hk brief` | Print a read-only repo brief without choosing validation commands; JSON includes Git worktree facts and handoff export status for dashboard/card integrations |
| `hk init` | Initialize ignored local Harness Kit state |
| `hk start demo-work --plan <text>` | Start a lifecycle work item and optionally seed context/plan records; same-slug retries resume the active work item |
| `hk work start` | Advanced compatibility surface for ledger-backed local work units |
| `hk note` | Advanced: append typed plan, background, learning, decision, gap, or spec-impact notes |
| `hk status` | Show active work, readiness checks, and next-action guidance for the agent loop |
| `hk sync` | Record or check a freshness checkpoint for the active work snapshot; use `--exclude PATH --reason TEXT` for explicit one-shot untracked local-state exclusions; HK records/revalidates excluded path metadata instead of using a tiny hardcoded allowlist |
| `hk capture` | Advanced: run a native command and record exact evidence |
| `hk artifact attach` | Attach a real harness/tool-produced file such as an agent session transcript, Codex review transcript, HAR file, or validation artifact; HK copies/references it, hashes it, and renders metadata in handoff/export |
| `hk artifact list` | Read-only list of attached artifacts for the active work; use after attach to verify kind, label, redaction, size, hash, and copied/reference path |
| `hk review prompt REVIEW_NAME` | Print a profile-named reviewer prompt from `hk status` / `hk checks --changed` to dispatch to an independent AI/tool or fresh-context reviewer, e.g. Pi `subagent`, Claude Code `Agent`/`Task` alias, or Codex via Shell tool running `codex review --uncommitted`; re-run `hk status` after review tools run |
| `hk review add --path src/foo.py ...` | Record a targeted follow-up review for one or more currently changed repo-relative paths; HK uses path/content facts to avoid whole-diff review thrash |
| `hk summary` | Render a concise human-readable readiness digest for PRs/review |
| `hk handoff` | Render a longer transfer artifact from the work ledger; `--json` returns live markdown content without writing files |
| `hk export --format handoff-dir` | Generate a compact committed handoff package such as `.ai/hk/2026-05-09-120000-demo/` from the HK ledger (`README.md`, `meta.json`, explicit-only `artifacts/`); active `.ai/hk/<work-id>/` exports are lifecycle-neutral for validation/review/sync freshness and readiness changed-path checks, and `--check --json` validates package freshness with structured fresh/missing/stale/invalid/no-active-work states while preserving nonzero exits for non-fresh exports |
| `hk spec` | Manage optional local/external spec drafts |
| `hk instructions` | Print the compact user-level `AGENTS.md` snippet; use `--scope repo` for a fuller profile-specific repo snippet |
| `hk profile list` | List built-in/custom/user-config profile contracts and model-directed selection guidance |
| `hk profile resolve` | Resolve the configured profile for a target using explicit user config bindings, including Git linked-worktree projection |
| `hk profile show <name>` | Show one profile's instructions, checks, and review guidance |
| `hk profile create <name>` | Create an editable custom profile TOML template |
| `hk config inspect` | Read-only snapshot of resolved `harness.toml`, target binding, profile, and active system-map source/status |
| `hk config validate` | Deterministically validate config/profile/system-map references; does not run profile commands or change readiness semantics |
| `hk config explain --changed\|--path PATH` | Explain why profile checks/reviews and system-map invariants surface for changed or explicit paths |
| `hk config audit` | Advisory read-only drift/surprise report for config joins; exits zero by default |
| `hk checks [--profile <name>] [--changed]` | Show named verification loops and review guidance without executing them; `--changed` adds path-rule suggestions, required items, matched files, and triggering patterns |
| `hk plan <text>` | Record or refine the lifecycle implementation plan for active Harness Kit work |
| `hk dangerously-skip review\|validation\|sync --label <name> --reason <text> --mitigation <text>` | Explicitly record an auditable dangerous skip when a lifecycle guarantee cannot be satisfied; skips render in summary, handoff, and PR handoff |

Portable plan-artifact commands have been removed from `hk`. New scaffolded
repositories use their native check/verify and verification-route contract. For
HK-native repos that want durable review artifacts, generate compact committed
packages with `hk export --format handoff-dir --output .ai/hk/2026-05-09-120000-demo`
instead of hand-authoring `.ai/plans` files. The export is a projection, not a
second ledger: `README.md` is the human handoff, `meta.json` is machine
freshness/integrity data, and `artifacts/` is for explicit copied attachments only; `--no-copy` attachments remain referenced by metadata. The active `.ai/hk/<work-id>/` package is generated/derived and does not by itself stale validation/review/sync freshness or readiness changed-path checks; validate export integrity with `hk export --format handoff-dir --check` or HK export integrity check.

Config diagnostics are intentionally narrower than authoring. They can inspect,
validate, audit, and explain deterministic joins between target bindings,
profiles, review prompt files, and system-map labels. They do **not** infer
architecture, draft authoritative profiles/system maps, execute validation, or
create readiness blockers. Use the profile/system-map authoring skills for
judgment-heavy create or audit/update proposals.

Profiles are small workflow contracts for agentic engineering checks and
reviews. They describe what exists for an environment; they do **not** run those
checks or reviews. Well-authored profiles also separate focused iteration checks
from final closeout gates so agents do not rerun broad validation and review
stacks after every small edit. Agents should run the suggested validation command
directly so the raw output stays visible in the normal shell loop, then record
the exact command/result with `hk validate --why` for Harness Kit lifecycle work.
When a profile check is named, record it with `hk validate --check NAME --why ...`.

Initial built-in profiles:

- `generic`
- `python`
- `go`
- `rust`
- `rust-mise`

Example discovery:

```bash
hk profile list --target /path/to/repo --json
hk checks --profile python --target /path/to/python-project --changed --json
```

`profile list --target` does not score, rank, or implicitly choose a profile. It
prints available profile contracts plus few-shot selection guidance for the
agent. Agents inspect the target scope, choose the closest profile, tell the user
once why they chose it, and then use that profile consistently. During
implementation, use focused profile checks and targeted validation; save broad
required gates and reviews for closeout once the implementation is stable. After
small review fixes, prefer targeted follow-up validation/review for changed paths
instead of rerunning the whole stack unless behavior or design changed. In
monorepos, `--target` should usually be the module/package/crate directory that
owns the work, not the repo root.

The selection order is conceptual, not algorithmic:

1. exact target/module profile, for example `my-project-api`
2. repo-specific profile, for example `foreman-root`
3. stack/task-runner profile, for example `python` or `rust-mise`
4. `generic`

For example, a mixed repo root with a Python manifest under a module such as
`packages/api` should use `--target packages/api` and choose `python` unless a
custom profile like `my-project-api` exists. A Rust repo or crate with `.mise.toml` and repo guidance
naming mise gates should choose `rust-mise` unless an exact module/repo profile
exists.

Custom profiles can be loaded either by declaring a profile directory in
`harness.toml`:

```toml
profiles_dir = "profiles"
# or, for more than one catalog:
profiles_dirs = ["profiles", "team-profiles"]
```

Paths are resolved relative to `harness.toml` unless they are absolute. HK loads
built-ins first, then inline `[profiles.<name>]`, then config-declared profile
directories, then an explicit CLI `--profiles-dir` when one is provided; later
sources override earlier profiles with the same name. This means a compact
`harness.toml` can keep only target bindings while profile bodies live in
separate files.

See [Profile Authoring](../how-to/profile-authoring.md) for guidance on choosing
`applies_when` vs `required_when`, avoiding expensive `required_when = ["*"]`
patterns, and bounding advisory reviews.

Custom profiles can also be loaded ad hoc with `--profiles-dir`:

```bash
hk profile create my-project-api \
  --target my_project/api \
  --preset python \
  --output ~/.config/harness-toolkit/profiles/my-project-api.toml

hk profile list \
  --target my_project/api \
  --profiles-dir ~/.config/harness-toolkit/profiles \
  --json

hk checks \
  --target my_project/api \
  --profile my-project-api \
  --profiles-dir ~/.config/harness-toolkit/profiles \
  --json
```

`profile create` creates an editable template only. It does not modify the target
repo, does not infer commands as facts, and refuses to overwrite an existing file
unless `--force` is passed.

This repo and generated harness-scaffold repos include a
`harness-kit-profile-authoring` skill that agents can load when no exact profile
exists. It guides agents to mine CI, hooks, task runners, and repo docs, then
propose TOML for user approval before writing a custom profile.

Harness Kit lifecycle commands accept:

- `--target PATH` — target repo or scoped path, defaulting to the current directory
- `--json` — machine-readable output where useful
- `--no-local-files` — use external state instead of checkout-local ignored files
  for commands that write lifecycle state

Commands that need custom profiles load directories declared in user
`harness.toml`; they also accept `--profiles-dir` for ad hoc catalogs. This keeps
profile catalogs explicit and avoids hidden repo-local adoption.

Agent-friendly properties in the current spike:

- non-interactive by default; every input is an argument or flag
- local state is ignored through `.git/info/exclude`
- profile/check discovery does not execute commands
- JSON output for every command agents need to compose
- actionable errors with a suggested retry command
- focused per-subcommand help with examples

## Current limitations

This is intentionally an early implementation:

- It does not install global mise tasks yet.
- It does not render `slice-plan` prompts from portable state yet.
- HK does not install global mise tasks yet; repos that adopt committed `.ai/hk` exports need a repo-owned sync-check task or CI hook to validate them.
- External state is keyed by git remote URL when available, otherwise by target path.

The spike proves that the workflow can be attached to an arbitrary repo without
making that repo dirty.

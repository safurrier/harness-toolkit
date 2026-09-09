---
id: harness-toolkit-spec
title: harness-toolkit Specification
description: >
  Correctness envelope for harness-toolkit — the requirements, contracts,
  and invariants that any valid implementation must satisfy.
index:
  - id: requirements
    keywords: [must, should, may, task-contract, init, check, ci, verify, plan]
  - id: interfaces
    keywords: [cli, mise, tasks, stack-protocol, shapes, config, plan]
  - id: invariants
    keywords: [ci-parity, golden-path, worktree, deterministic, stack-dispatch]
---

# harness-toolkit — Specification

> Correctness envelope for the Harness Engineering Toolkit. For how the system
> works now, see `docs/` (MkDocs site). For how to work in this repo, see
> `AGENTS.md`.

## Summary

harness-toolkit contains two related CLIs: `harness-scaffold`, the starter-template CLI for new agent-ready repositories, and `hk` / `harness-kit`, the portable workflow CLI for existing repositories. `harness-scaffold` transforms a cloned template into a fully configured project with a stable 22-task command surface. `hk` applies planning, validation, review, readiness, and handoff workflow state without committing scaffold files, and is evolving toward a cleaner lifecycle-first Harness Kit backed by local ledgers, sync checkpoints, captured command evidence, generated handoffs, and optional local specs. Both humans and AI agents benefit from language-agnostic, CI-parity contracts where `mise run check` is the fast local gate and handoff evidence stays inspectable.

## Goals / Non-Goals

**Goals:**

- Provide a stable, minimal command surface for humans and agents
- Support two repo shapes: single-project and apps workspace
- Keep orchestration thin — delegate to language-native tools
- Make CI call the same entrypoints as local usage
- Preserve "batteries included" capabilities from reference templates (python-collab-template, go-template-project)

**Non-Goals:**

- No Bazel/Buck2 (v1)
- No implicit auto-discovery of apps based on folder existence — configuration is explicit
- No mandatory spec folder layout beyond the generated defaults
- No specific agent runtime requirement (Claude Code, Codex, Pi, etc.)

## Requirements

### MUST

- `mise run init` supports interactive and non-interactive modes
- `mise run init -- --non-interactive` with explicit flags produces deterministic output
- All 22 task scripts exist in `.mise/tasks/`, are executable, and have `# MISE description=` headers
- `mise run check` passes on a freshly initialized project without manual intervention (golden path)
- `mise run ci` produces identical results to `mise run check` (CI parity)
- Pre-commit hooks call the same tasks as CI
- Non-interactive init fails fast with clear errors on missing required inputs
- Generated projects include `AGENTS.md`, `SPEC.md`, `docs/explanation/architecture.md`, `docs/explanation/decisions/`, and CI workflow
- All generated docs have valid YAML frontmatter with `id`, `title`, `description`, and `index` fields
- ADRs have Status (from allowed values), Context, Decision, and Consequences sections
- `mise run plan -- <slug>` creates a plan directory with META.yaml, TODO.md, LEARNING_LOG.md, VALIDATION.md, REVIEW.md, DECISIONS.md, and artifacts/manifest.yaml; invalid or duplicate slugs fail with clear errors
- `mise run slice-plan`, `slice-implement`, and `slice-review` render provider-neutral prompts into the active plan's `prompts/` directory
- `mise -q run slice-status -- --json` emits machine-readable active slice state
- Generated projects include `.ai/plans/` with routing AGENTS.md, templates, and example
- Generated projects include `.agent/skills/slice-workflow/` with artifact policy, handoff rubric, holdout sample tasks, and prompt templates
- Plan META.yaml has required fields: `slug`, `created` (YYYY-MM-DD), `status` (from allowed values)

### SHOULD

- `mise run check` completes in under 60 seconds for a single-project repo
- Init prompts have sensible defaults for every field
- Generated docs have machine-readable frontmatter index entries with keywords
- Adding a new stack requires changes in one file (stack module) plus templates

### MAY

- Support additional stack variants, such as alternate web UI or D1 access layers
- Support `workspace.toml` module registry for apps-shape repos
- Support custom task scripts via plugin directories

## Interfaces & Contracts

**Scaffold CLI:**

```
harness-scaffold init [OPTIONS]
  --non-interactive     Skip prompts, require all flags
  --name TEXT           Project name (required)
  --shape [single|apps] Repo shape (required)
  --stack [python|go|rust|web|blender|threejs] Primary stack (required)
  --modules TEXT        Comma-separated module names (apps shape)
  --go-module TEXT      Go module path (Go stack)
  --web-ui [plain|tailwind|shadcn]
                         Web UI variant (Web stack)
  --web-db [d1|drizzle-d1]
                         Cloudflare D1 access layer (Web stack)

Visual starters (`blender`, `threejs`) support `--shape single` only and reject
`--no-examples` before init because their reference scenes are intentional edit
seams rather than removable generic examples.
  --no-hooks            Skip pre-commit hook installation
  --no-examples         Remove example code after init
```

**Harness Kit CLI:**

Current `hk` commands are lifecycle-first. Portable plan-artifact
commands (`hk attach`, `hk legacy plan`, and `hk legacy sync-check`) are removed;
scaffold plan artifacts use `mise run plan` and `mise run sync-check` through the
slice-workflow CLI instead.

```
hk profile list --target <repo-or-module> --json
hk profile resolve --target <repo-or-module> --json
hk config inspect --target <repo-or-module> --json
hk config validate --target <repo-or-module> [--strict-labels] --json
hk config explain --target <repo-or-module> (--changed | --path <repo-relative-path>) --json
hk config audit --target <repo-or-module> --json
hk checks --target <repo-or-module> [--profile <profile>] [--changed] --json
```

The public shape is lifecycle-first rather than generic-note-first:

```
hk brief --target <repo-or-module> --json
hk start <slug> --plan "TEXT" --target <repo-or-module> --json
hk start <slug> --context "TEXT" --plan "TEXT" --target <repo-or-module> --json
hk status --target <repo-or-module> --json
hk plan "TEXT" --target <repo-or-module> --json
hk plan --from-file <path> --target <repo-or-module> --json
hk context "TEXT" --target <repo-or-module> --json
hk context --from-file <path|-> --target <repo-or-module> --json
hk decide "TEXT" --spec-impact none|updated|not-needed --spec-ref <path> --target <repo-or-module> --json
hk validate [--check <profile-check>] [--timeout-seconds N] [--max-log-bytes N] --why "WHAT THIS VALIDATES" --target <repo-or-module> -- <command...>
hk review prompt [profile-review] --target <repo-or-module> --json
hk review add [--review <profile-review>] [--path <repo-relative-path>]... --backend <independent-tool> --reviewer <independent-reviewer-or-fresh-context-subagent> --summary "TEXT" --target <repo-or-module> --json
hk artifact attach --path <file> --kind <kind> --label "TEXT" --target <repo-or-module> --json
hk artifact list --target <repo-or-module> --json
hk sync --exclude <path> --reason "TEXT" --target <repo-or-module> --json
hk sync --target <repo-or-module> --json
hk sync --check --target <repo-or-module> --json
hk dangerously-skip review|validation|sync --label <name> --reason "TEXT" --mitigation "TEXT" --target <repo-or-module> --json
hk ready --target <repo-or-module> --json
hk summary --target <repo-or-module> --json
hk handoff --target <repo-or-module> --format markdown|pr [--json]
hk export --target <repo-or-module> --format handoff --json
hk export --target <repo-or-module> --format handoff-dir --output .ai/hk/2026-05-09-120000-demo --json
hk export --target <repo-or-module> --format handoff-dir --output .ai/hk/2026-05-09-120000-demo --check --json
hk spec init|status|outline|promote --target <repo-or-module> --json
```

Slugs are short human-readable task names; chronological ordering comes from
HK-generated timestamped work IDs. `hk start --plan` starts work and records the
first lifecycle plan event; `hk plan` records or refines lifecycle plan text for
already-active Harness Kit work, including progressive planning when the detailed
implementation shape emerges after work starts. `hk brief --json` is the read-only
workspace/card surface and reports repo/scope, Git worktree facts, active work,
and handoff export status without writing files. `hk export --format handoff-dir
--check --json` MUST return structured expected-state JSON for fresh, missing,
stale, invalid, and no-active-work exports while preserving nonzero exits for
non-fresh states. `hk status` is the agent
next-action view; `hk summary` is the concise human-readable readiness digest;
`hk handoff` is the longer transfer artifact. Spec impact uses explicit modes (`none`, `updated`, or
`not-needed`) plus optional `--spec-ref` file references. Review is required by
default. Preferred review comes from an independent AI/tool reviewer, ideally a
different model, runtime, or context. A fresh-context subagent is the minimum
acceptable fallback. Implementation-agent self-review does not satisfy readiness;
if the harness provides a fresh-context review mechanism, the agent should dispatch
`hk review prompt` to it before handoff. Examples include Pi `subagent`, Claude
Code `Agent`/legacy `Task`, and Codex via the Shell tool running
`codex review --uncommitted`. Agents should re-run `hk status` after review
because review tools may create agent-local state. Reviews record deterministic
path/content facts for the reviewed changed paths. Validation evidence also records
path/content facts for changed paths when captured; exact diff hashes remain a
sufficient freshness proof and backward-compatible fallback, but path/content
coverage can keep evidence fresh when unrelated or generated files changed.
Readiness may accept multiple targeted follow-up reviews when their reviewed paths
cover the current review-relevant diff. Required profile check labels remain
authoritative: generic or differently labeled validation evidence may explain
freshness in `hk status`, but it does not satisfy a required profile check unless
it was recorded under that required label or explicitly skipped. Generated active
HK export refreshes under `.ai/hk/<active-work-id>/...` are derived lifecycle
artifacts: they must not by
themselves make validation, review, or sync freshness stale, and their integrity
is checked by `hk export --format handoff-dir --check` / `mise run sync-check`
instead. If no independent AI/tool or fresh-context review is available, the
agent must use an explicit dangerous review skip with a label, reason, and
mitigation. If sync freshness is stale only because of
understood untracked local-only state, the agent should prefer a constrained
`hk sync --exclude PATH --reason ...`; exclusions are recorded and revalidated
rather than limited to a hardcoded `.pi`/`.claude` allowlist, while root,
pathspec, tracked, staged, and missing paths remain invalid. Whole-sync dangerous
skips remain an explicit fallback.

`hk profile resolve`, `hk config inspect`, `hk config validate`, `hk config explain`,
`hk config audit`, `hk checks --changed`, and `hk status` MUST explain profile/check/review
selection and evidence freshness without changing readiness semantics. `hk status`
MUST expose typed freshness diagnostics for agents, including generic no-profile
validation/review freshness, profile-label freshness when profile items are
required, stale/uncovered paths, evidence counts, and active export neutrality
notes. Config diagnostics are read-only:
they MUST NOT generate authoritative profiles/system maps, execute profile
commands, run reviewers, or become hidden readiness gates. JSON diagnostics may
grow only additively and should include the profile match kind plus changed
files/patterns that triggered suggested or required profile items. Suggested
profile reviews are non-blocking status guidance; required profile reviews remain
readiness checks. Profile reviews are named review policies with optional inline
or file-backed `instructions`; HK renders those instructions but does not run
reviewers or load skills/plugins itself.

`hk artifact attach` records harness/tool-produced files such as agent session
transcripts, Codex review transcripts, HAR files, or raw validation artifacts by
copying or referencing the source file, hashing it, and appending metadata to the
Harness Kit lifecycle ledger. `hk artifact list` is a read-only inspection surface
for those attachments. Handoff-dir exports include copied attached artifacts under
explicit-only `artifacts/` and record their metadata; referenced `--no-copy`
artifacts stay referenced by metadata only. Agents should attach real files
produced by tools rather than narrating their own session text into HK.

Captured validation evidence may bound process runtime and transcript size with
`--timeout-seconds` and `--max-log-bytes`. Timeout and truncation are part of the
evidence record, not hidden harness behavior. Non-raw live output and transcripts
MUST apply the same built-in redaction guarantees across stream chunk boundaries;
long delimiter-free live output may be suppressed rather than buffered without
limit, while transcript capture remains governed by the transcript byte cap.

Profiles and repo-owned scripts are validation guidance and stable native command
surfaces for `hk validate`, not task-runner commands that HK chooses and runs.
Lower-level work/note/capture/evidence commands may remain as compatibility or
advanced interfaces, but Harness Kit is not complete until lifecycle readiness reaches
parity with the plan-artifact workflow.

`harness-kit` is the readable long command for the same portable CLI. `hk` is the
short daily command.

**22-task contract:**

| Task | Purpose | Composition |
|------|---------|-------------|
| `init` | Transform scaffold into project | One-time, destructive |
| `setup` | Install dependencies | `uv sync` / `go mod download` |
| `fmt` | Auto-format | `ruff format` / `gofumpt` |
| `lint` | Lint check | `ruff check` / `golangci-lint` |
| `typecheck` | Type analysis | `ty check` / `go vet` |
| `test` | Unit tests | `pytest` / `go test` |
| `build` | Produce artifacts | Stack-dependent |
| `check` | Fast quality gate | fmt-check + lint + typecheck + test |
| `dev` | Local development | Stack-dependent |
| `ci` | CI entrypoint | Delegates to `check` |
| `docs` | Documentation server | MkDocs dev server |
| `plan` | Create plan directory | Scaffolds `.ai/plans/<slug>/` |
| `plan-check` | Validate plan metadata | Checks active or explicit plan files |
| `spec-check` | Validate decision promotion | Checks ledger/ADR reflection |
| `evidence-check` | Validate evidence artifacts | Checks validation commands and manifest |
| `review-check` | Validate review artifact | Checks external-enough review fields |
| `sync-check` | Handoff readiness gate | Runs active, explicit, or changed-plan checks |
| `slice-plan` | Render planner prompt | Writes `prompts/planner.md` |
| `slice-implement` | Render implementer prompt | Writes `prompts/implementer.md` |
| `slice-review` | Render reviewer prompt | Writes `prompts/reviewer.md` |
| `slice-status` | Show active slice state | Text or JSON status |
| `verify` | Heavy validation | Integration, docker, security |

**Stack Protocol:**

```python
class Stack(Protocol):
    def init_single(self, root: Path, config: Config) -> dict[str, str]: ...
    def init_module(self, mod_dir: Path, config: Config, mod_name: str) -> dict[str, str]: ...
    def remove_examples(self, root: Path, config: Config) -> None: ...
    def remove_module_examples(self, mod_dir: Path) -> None: ...
    def tools_toml(self) -> str: ...
    def adr_notes(self) -> str: ...
    def stack_notes(self) -> str: ...
```

## Invariants

- **CI parity**: `mise run check` locally MUST match the CI quality gate, and CI MUST also run `mise run sync-check` for handoff-contract coverage. Pull request CI MUST validate changed completed plans with `sync-check --changed-plans`. Pre-commit hooks call the same quality tasks. Violation causes green-local/red-CI divergence or missing handoff evidence.
- **Golden path guarantee**: A freshly initialized project (`mise run init`) MUST pass `mise run check` out of the box. Violation breaks first-run experience.
- **Worktree safety**: All tasks must run from a clean checkout or Git worktree. No reliance on absolute paths, mutable global state, or undeclared local artifacts.
- **Stack dispatch via env**: Tasks read `SCAFFOLD_PROJECT_STACK` from `.mise.toml` to dispatch to the correct toolchain. Wrong dispatch = wrong tools run.
- **Deterministic output**: Non-interactive init with identical inputs produces identical output. Template rendering is deterministic.
- **stdlib-only test helpers**: `_docs_helpers.py` uses only stdlib (no pyyaml) so it's portable into generated repos without adding dependencies.
- **Lifecycle-first Harness Kit**: Harness Kit MUST preserve the handoff-safety spine: useful context when it prevents rediscovery, explicit plan, spec/decision reflection, validation evidence, external-enough review, readiness gate, and handoff artifact. A generic note ledger without readiness parity is an implementation foundation, not the completed product.
- **Shell-first command evidence**: `hk` MAY capture exact native commands and local work state, but MUST NOT hide validation behind `hk run`-style task-runner commands. Captured evidence preserves command identity, exit code, rationale, transcript metadata, timeout/truncation metadata, and redaction boundaries. Profiles and dumb scripts may guide which native commands to validate, but the proof remains `hk validate --why ... -- <native command>`.
- **Internal Git client seam**: trusted Git queries inside `harness_toolkit.kit` MUST go through `kit.git.client.GitClient`; arbitrary command evidence capture stays isolated in `kit.capture.process`. Domain logic such as diff hashing, sync exclusion safety, profile resolution, and readiness remains in the existing semantic modules instead of becoming generic Git abstractions.
- **Freshness vs readiness**: `hk sync --check` answers whether ledger work changed after the last checkpoint. `hk ready` is the ledger-backed Harness Kit lifecycle readiness gate. `mise run sync-check` validates committed handoff artifacts: legacy scaffold/task-contract plan artifacts and HK `.ai/hk/<work-id>/` export packages when present.
- **No heuristic readiness/profile scoring**: `hk brief` and profile commands report facts and guidance, not readiness grades, confidence scores, or silent validation command selection. Planning may happen outside HK, but agents must translate the agreed intent into explicit lifecycle records; HK records those declarations and checks evidence consistency while humans/reviewers judge quality. HK does not infer whether context is non-obvious; agents record `hk context` when it improves handoff or prevents rediscovery.
- **Profile catalog ergonomics**: user config MAY load standalone profile TOML from `profiles_dir` / `profiles_dirs` while retaining explicit target bindings. Profile resolution MUST prefer direct longest-prefix target matches, then MAY project configured target bindings across Git linked worktrees that share the same common Git directory; it MUST NOT silently select profiles for separate clones based only on matching remote URLs. Profile path rules MUST accept both Git repo-root-relative changed paths and target-relative paths for scoped module profiles, while reporting matched paths in repo-root-relative form. Profile authoring guidance SHOULD distinguish focused iteration checks, final closeout gates, CI/heavy parity checks, handoff/export checks, required reviews, and advisory reviews so agents avoid repeated broad validation/review loops without weakening readiness blockers for risk-specific paths.
- **HK export views**: HK ledger state is the canonical lifecycle source for Harness Toolkit repo work. Committed `.ai/hk/<work-id>/` directories, when present, MUST be generated review/handoff packages from `hk export --format handoff-dir`. The default package is intentionally compact: `README.md` is the single human projection, `meta.json` stores freshness/integrity metadata (`work_id`, git SHA, diff hash, event/evidence counts, generated file hashes), and `artifacts/` is explicit-only. Hand-authored `.ai/plans` slices are legacy/scaffold-generated-repo compatibility artifacts, not the normal Harness Toolkit repo workflow.
- **Local-first adoption boundary**: default `hk` local assistant state stays ignored or external. Committed `.harness/`, `SPEC.md`, generated `.ai/hk` exports, or task-contract artifacts require explicit adoption/promotion.

## Acceptance

```bash
mise run check          # fast: fmt-check + lint + typecheck + all tests
mise run sync-check     # handoff: plan/spec/evidence/review contract
mise run verify         # heavy: integration, e2e, docker (when applicable)
```

Contract tests verify structural invariants (task files, doc schemas, template sections).
Golden output tests verify deterministic rendering across all 4 shapes (Python single/apps, Go single/apps).
E2E tests verify the full init → setup → check pipeline produces passing projects.

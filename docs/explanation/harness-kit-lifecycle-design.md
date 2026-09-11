---
id: harness-kit-lifecycle-design
title: Harness Kit Design
description: >
  Lifecycle-first Harness Kit design, including the ledger-backed state,
  evidence, readiness, sync checkpoints, optional specs, profiles, and rollout plan.
index:
  - id: thesis
    keywords: [hk, shell-first, lifecycle, readiness, ledger, evidence]
  - id: cli-contract
    keywords: [start, plan, decide, validate, review, ready, handoff]
  - id: rollout
    keywords: [staged, breaking, parity, fixtures, validation]
---

# Harness Kit Design
> **Historical note:** The generated slice-plan workflow described below was retired for new projects by [ADR 0014](../reference/decisions/0014-retire-slice-plans.md). Existing generated repositories remain legacy.


## Status

Draft implementation design, amended by
`docs/reference/decisions/0009-harness-kit-lifecycle-first-cli.md` after product review. This is
the repo-local companion to the vault note `Harness Kit SPEC.md`.

The current implementation is a useful ledger/capture foundation, but it should
not be treated as the full Harness Kit product until the lifecycle-readiness contract
is first-class.

## Thesis

Harness Kit is a cleaner, simpler handoff-safety lifecycle.

It should not make agents use a worse shell. It should preserve the original
workflow spine with less ceremony:

```text
plan → spec/decision reflection → validation evidence → external-enough review → readiness gate → handoff artifact
```

The ledger is the implementation substrate, not the primary product story. Harness Kit should give agents and humans:

- a concise repo map;
- explicit lifecycle records for context, plan, decision/spec reflection,
  validation, review, readiness, and handoff;
- exact command evidence;
- generated human-readable views;
- sync checkpoints that force reconciliation;
- optional local/external specs;
- profile guidance without heuristic auto-selection;
- explicit promotion boundaries for committed artifacts.

## Product boundaries

### `hk`

`hk` is the lifecycle assistant for existing and scaffolded repos. It owns repo
briefing, local/external harness state, work ledgers, lifecycle records, command
evidence, sync checkpoints, readiness checks, handoff rendering, optional local
specs, and profile listing/showing/creation.

It does not own universal task execution, validation command selection, readiness
scoring, automatic repo adoption, or issue-tracker orchestration.

### `harness-scaffold`

`harness-scaffold` remains the greenfield path for harness-ready repos. A later
phase may prototype a canonical scripts adapter contract as an alternative or
companion to the current generated mise task contract.

### Future orchestrator

Future orchestration is deferred. Harness Kit should produce state and evidence contracts
that an orchestrator could consume later without implementing daemons, dashboards,
or tracker polling now.

## Non-goals

- Do not add `hk run test`, `hk run check`, or other task-runner UX.
- Do not make `hk` choose validation commands through heuristic scoring.
- Do not create readiness scores or grades.
- Do not create a second durable guide competing with `AGENTS.md`.
- Do not force existing repos to commit `.harness/`, `.agent/`, `.ai/`, scripts,
  or `SPEC.md`.
- Do not require heavy planning ceremony for small changes.
- Do not implement Web/TypeScript scaffold in the core `hk` lifecycle rollout.
- Do not implement future orchestration in the lifecycle launch.

## Follow-up backlog

These are intentionally not part of the Harness Kit launch slice:

- add a few concrete `hk review add` examples once review dogfood settles;
- decide whether `.agent/skills/hk-session-artifacts` should remain repo-local or
  ship with generated templates;
- consider `hk artifact candidates` only if the skill helper proves too hidden or
  too manual;
- revisit repo-level `.harness/harness.toml` after user-local profiles get real
  use;
- add review dispatch/backfill helpers only when the shell-first prompt workflow
  is too slow or ambiguous; HK should still record externally produced review
  evidence rather than own reviewer execution.

## Design decisions

### Local state may be rich

Local standardization is allowed. The dangerous boundary is committing generated
ceremony to shared repos.

Default local state may contain ledgers, artifacts, generated Markdown views, and
local specs. Those files remain ignored/local unless explicitly promoted.

### Ledger-backed work model

The canonical work state is append-only JSONL, not a required bundle of Markdown
files. The public CLI should still read as lifecycle verbs rather than a generic
note/event ledger.

```text
<harness-state>/work/<timestamp>-<slug>/
  events.jsonl
  evidence.jsonl
  artifacts/
  views/                 # generated/materialized, not canonical
```

Generated views may include `learning-log.md`, `decisions.md`, `gaps.md`, and
`handoff.md`, but the ledger remains the source of truth.

### Typed notes are lower-level lifecycle records

Planning may happen outside HK in a human/AI conversation, issue, scratch doc, or
research pass. Agents should translate the agreed result into an explicit HK
lifecycle record instead of asking HK to parse the conversation heuristically.
Typed notes are useful as a storage and compatibility layer, but the common user
path should be lifecycle-oriented commands such as `hk context`, `hk plan`,
`hk decide`, and `hk validate`.

Context, plan, learning, decisions, gaps, and spec impact are typed records.
The public lifecycle command should be `hk context`, because HK is doing context
engineering for the next human or agent. It should stay lightweight and
agent-guided: the agent records context when it prevents rediscovery or clarifies
constraints, relevant files, assumptions, or repo facts. HK should not try to
infer when context is non-obvious, and it should not force filler records for
obvious small changes. Lower-level note/event storage may keep `background` as an
internal or compatibility alias when needed.

```bash
hk start auth-timeout-fix --plan "Update session timeout handling and validate focused auth tests."
hk context "Relevant files: src/auth/session.py and tests/test_session.py."
hk plan "Refined plan after discovery: preserve retry count semantics."
hk plan --from-file /tmp/adopted-plan.md
hk note --kind learning "Auth timeout behavior is owned by session refresh."
hk decide "Preserved retry count semantics." --no-spec-impact
hk note --kind gap "Full suite not run."
```

### Evidence is exact command capture

`hk capture -- <command>` runs native commands while recording proof. It must not
abstract the command into `hk run`.

Required evidence fields include command display, argv or shell command, cwd,
target scope, branch, git SHA, dirty state before/after, timestamps, duration,
exit code, transcript path, timeout/truncation metadata, transcript byte count,
and redaction metadata. Failed commands are evidence.

`hk validate` and `hk capture` can bound execution and evidence volume with
`--timeout-seconds` and `--max-log-bytes`. These bounds must preserve the command
identity and result: a timeout records a timeout exit status and marker, and a
truncated transcript records truncation metadata instead of pretending the full
log was captured.

### Capture redaction is pluggable

Capture includes a redaction interface: no env capture by default, log caps, a
built-in lightweight redactor, `--no-log`, an explicit `--raw-log`, and optional
external scanner configuration. Non-raw live output must not be weaker than the
stored transcript: redaction must preserve enough stream context to avoid leaking
secrets split across read boundaries, while bounding live buffering for huge
newline-free output. Candidate scanner tools include `scrubadub`,
`detect-secrets`, `gitleaks`, and `trufflehog`.

### Sync is a checkpoint/freshness bit

`hk sync` is not a semantic quality validator. It is a stop-and-reconcile
checkpoint.

Default behavior:

- print a short reconciliation checklist;
- append a `sync_checkpoint` event;
- store event sequence, git SHA, diff hash, evidence count, and note count;
- make `hk sync --check` binary: synced or needs sync.

Events after the last sync or a changed diff hash make the work unsynced.
Generated views such as handoffs and materialized Markdown are sync-neutral
because they do not change the substance of the work. If a final freshness check
is stale only because of understood local agent state, the user should prefer
`hk sync --exclude PATH --reason TEXT`; the exclusion is recorded with path
metadata and revalidated. `hk dangerously-skip sync --label NAME --reason TEXT
--mitigation TEXT` remains a fallback for cases where a constrained exclusion is
not appropriate. Validation/review freshness accepts unchanged source diffs across
agent-local sync skips so local-only state does not force false stale evidence.

Adopted/scaffolded repos may configure stricter checks later.

### Readiness is separate from sync freshness

The current scaffold task contract uses native quality and product-verification
commands, not plan-artifact readiness checks. New generated repositories run
`mise run check` for quality and `mise run verify` for heavier, path-selected
product proof. Existing generated repositories that retain plan artifacts are
legacy; Harness Kit's own `hk ready` remains the lifecycle handoff gate.

The target split is:

- `hk sync --check`: answers "has work changed since the last checkpoint?"
- `hk ready`: answers "is this work ready to hand off?"

`hk ready` validates explicit ledger declarations, not inferred semantic quality.
Agents choose plans, commands, and review instructions; HK records and checks that
required declarations are present, internally consistent, and renderable.

### Agent work lifecycle

Harness Kit should teach the workflow as a journey rather than dump every command at
once. The primary reader is an implementation agent. The human usually sets up a
small `AGENTS.md` directive, plans the change through normal back-and-forth, then
hands the agreed intent to an agent and says to use `hk`.

The happy path is short:

```bash
hk start <slug> --plan 'Adopted implementation intent'
# implement normally
hk validate --why 'What this command proves' -- <native command>
hk status
hk ready
hk handoff
```

`hk status` is the guide through the rest of the journey. It can ask for context,
decision/spec reflection, review, sync reconciliation, or an explicit dangerous
skip. This keeps the agent from memorizing a long checklist while preserving the
handoff guarantees.

The underlying lifecycle remains phase-oriented:

1. **Context** — read repo background, inspect specs/instructions, and record
   stable framing, constraints, relevant files, and discovered repo facts with
   `hk context` only when it prevents rediscovery.
2. **Plan** — planning may happen in chat or external docs first; record the
   agreed implementation intent as a compact plan note, with optional tasks only
   when a checklist is useful.
3. **Implement** — edit code in the normal shell/editor loop; record notable
   decisions and spec impacts.
4. **Validate** — run native repo commands directly and capture exact evidence
   with a rationale for what each command proves.
5. **Review** — record external-enough reviews with backend, reviewer,
   profile review name when applicable, findings, and disposition. Multiple named
   reviews should be possible over time, such as core quality, repo conventions,
   design, security, UX, or technology-specific best practices.
6. **Handoff** — run sync/readiness checks and render a conservative handoff.

The current scaffold artifacts map to those phases as follows:

| Phase | Legacy plan artifact (existing generated repos) | Harness Kit target |
|---|---|---|
| Context/research | `LEARNING_LOG.md` | `hk context` / learning records |
| Plan | `TODO.md`, `IMPLEMENTATION.md` | `hk plan` plus optional task/checklist records only when useful |
| Decisions/spec | `DECISIONS.md`, ADR/ledger links | `hk decide` and spec-impact reflection records |
| Validation | `VALIDATION.md`, `artifacts/manifest.yaml` | `hk validate --why ... -- <command>` captured evidence |
| Review | `REVIEW.md` | `hk review add` records with backend/reviewer/profile-review/findings/disposition |
| Handoff gate | HK export integrity check | `hk ready` plus `hk sync --check` |

This keeps Harness Kit shell-first while making the plan package an optional
exported view of the ledger rather than the canonical source of truth. Harness Kit is
only complete once the lifecycle commands exist together: start, plan/context,
validate, review, sync, ready, and handoff.

### Profiles and dumb scripts guide validation; they do not run it

Keep profile UX explicit and guidance-oriented:

```bash
hk profile list --target . --json
hk profile resolve --target . --json
hk profile show generic --json
hk checks --target . --json
hk profile create <name> ...
```

Do not add heuristic command mining or auto-selected profile recommendations.
Explicit user config resolves a target path to a profile by longest path prefix.
If no literal path matches, HK may use Git worktree metadata to project configured
target bindings across linked worktrees that share the same common Git directory;
this is path binding reuse, not command inference. Separate clones with the same
remote URL should not silently inherit a profile. `hk brief` may report facts such
as `.mise.toml`, `scripts/check`, and CI files, but must not claim a recommended
command or confidence score.

Profiles and dumb repo scripts fit into Harness Kit as guidance and stable native
command surfaces for `hk validate`, not as a task-runner layer. Internal trusted
Git queries use the small `kit.git.client.GitClient` seam, while arbitrary
user/agent command evidence remains isolated in `kit.capture.process`; do not
merge these two subprocess domains. A user-level `harness.toml` can bind known
repo/module paths to inline profiles or to standalone profiles loaded from
`profiles_dir`:

```toml
[[targets]]
name = "foreman"
path = "~/git_repositories/foreman"
profile = "foreman"

[profiles.foreman]
title = "Foreman"
summary = "Rust CLI/TUI project."
target_hint = "~/git_repositories/foreman"
instructions = "Use focused cargo tests and Codex review when useful."

[[profiles.foreman.checks]]
name = "cli-config-tests"
purpose = "Run CLI config tests."
command_template = "cargo test --test cli_config"
run_from = "repo-root"

[[profiles.foreman.reviews]]
name = "core-quality"
purpose = "Fresh-context review before handoff."
backend = "codex"
dispatch_hint = "codex review --uncommitted"

[profiles.foreman.reviews.instructions]
type = "inline"
text = "Review correctness, regression coverage, and handoff clarity."
```

Review entries are guidance just like checks: agents dispatch them via the current
harness and record accepted results with `hk review add`; HK does not launch them.
Review instructions can be inline or file-backed, including wrapper prompts that
tell a fresh reviewer to load a skill or checklist.
When a repo wants committed handoff artifacts, `hk export --format handoff-dir
--output .ai/hk/2026-05-09-120000-demo` writes a compact generated package from
the ledger. The ledger remains the source of truth; the package should not become
a Markdown mirror of every ledger event type. By default, `README.md` is the
human review/handoff document, `meta.json` is machine freshness/integrity data,
and `artifacts/` is reserved for explicit durable attachments.
Profiles are not the same thing as `.harness/harness.toml`: a profile is named
validation/review workflow guidance, while `.harness/harness.toml` is the future
optional committed repo config/adoption root that can select defaults, policies,
and repo-specific profile locations. Path rules may be repo-root-relative or
relative to the selected module `--target`, which keeps subdirectory profiles
natural to author while still rendering matched paths in Git's repo-root-relative
form. For example, `hk profile show python` or
`hk checks` may point an agent at `mise run check`, `uv run pytest`, or
`scripts/check`, but the proof should still be captured as:

```bash
hk validate --why "Full repo quality gate." -- mise run check
hk validate --why "Focused regression coverage." -- uv run pytest tests/unit/test_harness_kit_2.py -q
```

`hk ready` may use profile guidance to explain missing evidence kinds, but it
checks explicit captured evidence rather than silently choosing or running
commands.

### Specs can be local/external before committed

Random existing repos can get useful spec context without committing `SPEC.md`.
Committed `SPEC.md` wins when present; local/external specs are labeled drafts;
promotion is explicit and should dry-run before writing.

### Committed config root is `.harness/`

Use `.harness/` for committed harness config when a repo opts in. `AGENTS.md`
remains the durable instruction map. `.agent/skills/` remains the skill root.

## CLI contract

Target lifecycle-first commands:

```bash
hk brief [--target PATH] [--json|--markdown]
hk start <slug> [--context TEXT] [--plan TEXT] [--target PATH] [--json]
hk status [--target PATH] [--json]
hk plan "TEXT" [--target PATH] [--json]
hk plan --from-file PATH [--target PATH] [--json]
hk context "TEXT" [--target PATH] [--json]
hk context --from-file PATH|- [--target PATH] [--json]
hk decide "TEXT" [--spec-impact none|updated|not-needed] [--spec-ref PATH]... [--target PATH] [--json]
hk validate --why "WHAT THIS VALIDATES" [--kind KIND] [--target PATH] -- <command...>
hk review add [--review PROFILE_REVIEW] --backend NAME --reviewer INDEPENDENT_OR_FRESH_CONTEXT_REVIEWER --summary TEXT [--disposition TEXT] [--path REPO_RELATIVE_PATH]...
hk review prompt [--target PATH] [--json]
hk artifact attach --path FILE --kind KIND [--label TEXT] [--no-copy] [--target PATH] [--json]
hk artifact list [--target PATH] [--json]
hk sync [--exclude PATH]... [--reason TEXT] [--target PATH] [--json]
hk sync --check [--target PATH] [--json]
hk dangerously-skip review|validation|sync --label NAME --reason TEXT --mitigation TEXT [--target PATH] [--json]
hk ready [--target PATH] [--json]
hk summary [--target PATH] [--json]
hk handoff [--target PATH] [--format markdown|pr] [--write PATH] [--json]
hk spec init|status|outline|promote
hk profile list|show|create
```

`hk start --plan` is the promoted way to cut a slice with the first lifecycle
plan already recorded. `hk plan` remains the refinement command for already-active
work. Slugs are short human-readable names; timestamped work IDs provide ordering.
`hk status` is a preflight/next-action coach, `hk summary` is a concise
human-readable readiness digest for PRs/review, and `hk ready` remains the final
handoff gate.

`hk decide` records a structured spec-impact mode. `none` means no product/docs
impact was declared, `updated` means relevant specs/docs were updated or verified,
and `not-needed` means the change does not need spec/docs updates. `--spec-ref`
links the declaration to specific files without asking HK to infer correctness.

`hk sync --exclude PATH --reason TEXT` records a constrained checkpoint that
ignores only explicit untracked local-only paths. Exclusions are not limited to a
hardcoded `.pi`/`.claude` allowlist; the safety boundary is that HK records
excluded path metadata, rejects root/pathspec/absolute/tracked/staged/missing
paths, revalidates stored exclusions, and passes readiness only while
non-excluded work remains unchanged. It renders under `## Sync exclusions`, not
dangerous skips. Use `hk dangerously-skip sync` only when a constrained checkpoint
is not appropriate.

`hk artifact attach` is the generic way to attach real files produced by harnesses
or tools: Pi session transcripts, Codex review transcripts, browser HAR files, or
raw validation artifacts. HK copies or references the source file, records size and
sha256 metadata in the ledger, renders attached artifacts in handoff, and includes
copied attachments in handoff-dir exports under explicit-only `artifacts/`. `hk
artifact list --json` is the read-only inspection surface agents should use after
attachment. Agents should attach files produced by tools rather than writing their
own session prose into HK.

`hk review add` is intentionally not a self-review note. Review is required by
default. Preferred review comes from an independent AI/tool reviewer, ideally a
different model, runtime, or context. A fresh-context subagent is the minimum
acceptable fallback. Implementation-agent self-approval must fail readiness.
`hk review prompt` prints a copy-paste prompt for that reviewer. If the harness
has a fresh-context review mechanism, the implementation agent should dispatch
that prompt to it before handoff. Examples include Pi `subagent`, Claude Code
`Agent`/legacy `Task`, and Codex via the Shell tool running
`codex review --uncommitted`. Agents should re-run `hk status` after review because
review tools may create agent-local state. HK records deterministic path/content
facts for reviewed changed paths. Later small fixes can be covered by targeted
follow-up records with `hk review add --path PATH ...`; generated active HK export
refreshes are lifecycle-neutral for validation/review/sync freshness and readiness
changed-path checks, and should be
validated with export/sync checks, not another broad review or sync loop. See
[ADR 0011](../reference/decisions/0011-path-aware-review-freshness.md) for why review
freshness is path/content-aware rather than exact whole-diff matching, and
[ADR 0012](../reference/decisions/0012-lifecycle-neutral-active-hk-exports.md) for the active
export projection boundary. If review
is impossible, the agent must record `hk dangerously-skip review --label NAME --reason TEXT --mitigation TEXT`,
which is auditable and renders in summary and handoff. Future review-source config is
deferred.

Lower-level commands should not be equally promoted when a lifecycle command
exists. If a redundant command is only marginally useful, prefer cutting it or
explicitly marking it advanced.

```bash
hk work start|status|materialize        # advanced work-state surface
hk note --kind ...                      # advanced event entry, if retained
hk capture ... -- <command...>          # lower-level command evidence
hk evidence list                        # inspection/debugging
hk export --format handoff [--target PATH]
```

Portable plan-artifact commands have been removed from `hk`. New scaffolded
repositories use native `mise run check` and `mise run verify` with optional
named verification routes chosen explicitly by an agent or engineer; only legacy
generated repositories retain the
separate slice-workflow CLI.

Deferred commands also include state cleanup, deep spec impact, profile
validation, skill validation, and compatibility link helpers.

## State model

Default local state:

```text
.harness-local/harness-kit/
  state.json
  work/
  spec/
```

The path is ignored through `.git/info/exclude`, not committed `.gitignore`.

External state uses:

```text
$XDG_STATE_HOME/harness-toolkit/repos/<repo-key>/<scope>/
```

with `~/.local/state/harness-toolkit/repos/<repo-key>/<scope>/` as fallback.

Future committed/adopted config uses:

```text
.harness/
  harness.toml        # repo adoption/config: defaults, policies, selected profiles
  profiles/           # optional repo-specific profile definitions
  workflows/
  checks/
  schemas/
```

## Brief model

`hk brief` is read-only and must leave the worktree clean. It reports target
root/scope, branch/SHA/dirty state, visible harness state, AGENTS/SPEC presence,
profile catalog summary, common repo surfaces, active work status, and sync
status.

Evidence summaries are a planned follow-up once the evidence model stabilizes.

It must not choose validation commands, auto-select profiles, emit confidence
scores, or mutate state.

## Handoff model

Failed evidence in `hk handoff` should read as an attempted validation, not as a
successful validation claim.

`hk handoff` renders a conservative summary from ledgers and git facts. The
initial implementation includes target/branch state, typed decisions, learning
entries, gaps, captured evidence, failed commands, sync status, and spec-impact
notes. If no validation evidence exists, it says so.

Changed-file summaries, manual evidence labels, review focus, and continuation
notes are planned follow-ups.

## Rollout strategy

This is a staged breaking change. Compatibility does not need to be preserved
as a product promise, but the ledger workflow should not replace plan artifacts
until Harness Kit closes the readiness gaps that HK export integrity check currently
covers.

Each phase must include behavior-focused tests and parity fixtures where
conceptually relevant.

Each implementation phase must:

1. create/use an `hk` plan/work slice;
2. add fixture-based validation before or alongside implementation;
3. run local validation;
4. update plan evidence;
5. participate in final external review before PR.

## Phase plan

1. Canonical design/spec/ADR.
2. Read-only `hk brief`/inspection.
3. Local state + work ledger + typed notes.
4. Sync checkpoint.
5. Capture evidence + redaction prototype/interface.
6. Handoff/exported views.
7. Optional local/external SPEC.
8. Scaffold task-contract prototype.
9. Readiness parity with plan artifacts:
   - compact plan records and optional task/checklist events;
   - validation evidence rationale;
   - review events with backend/reviewer/profile-review/findings/disposition;
   - `hk ready`;
   - plan-directory export from the ledger as a future compatibility feature.
10. Docs/release/public cutover.

## Validation philosophy

Validation must be fixture-heavy and behavior-focused.

Fixture repos should cover generic git repos, Python/uv repos, Rust/mise repos,
the current harness-toolkit repo shape, monorepo scoped targets, repos with
committed specs, repos with local/external specs, and repos with no specs.

Test layers:

- unit tests for state resolution, event appending, JSON schemas, and sync
  freshness;
- golden tests for brief, handoff, and exported Markdown;
- E2E tests for clean worktree, overlay/external state, capture success/failure;
- parity tests comparing current concepts to lifecycle behavior where
  applicable.

## Acceptance criteria

- `hk brief` works without state and leaves the repo clean.
- `hk init` is idempotent and supports local/external state.
- `hk work start` creates an active ledger-backed work unit.
- `hk note` records typed note events.
- `hk sync` records a checkpoint; `hk sync --check` is freshness-based.
- `hk capture` preserves command identity, streams output, records exit code, and
  writes redacted evidence by default.
- `hk handoff` renders conservative Markdown/JSON without validation overclaims.
- `hk spec init --local` creates non-committed spec context.
- No default command commits harness artifacts to arbitrary existing repos.
- No command adds readiness scores or heuristic profile recommendations.

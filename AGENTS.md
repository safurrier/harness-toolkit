# harness-toolkit

**When a user corrects you or gives repo-specific tribal knowledge, document it
in the closest `AGENTS.md` before continuing.**

harness-toolkit contains two related CLIs. `harness-scaffold` is the
starter-template CLI: it generates projects with a stable mise task contract,
native quality and product-verification checks, plus stack templates. `hk` / `harness-kit` is the portable CLI
for applying the workflow to existing repos without committing scaffold files.
Generated repos receive a skill-local uv CLI, while `mise run slice-*` remains
the stable operator interface.

## How to Work Here

The local checkout path is `~/git_repositories/harness-toolkit`; older notes or
session summaries may still refer to the pre-rename path `~/git_repositories/agent-scaffold`.

Use Harness Kit (`hk`) as the canonical workflow for this repo: `hk start
demo-work --plan "..."`, record validation with `hk validate`, record
external-enough review with `hk review add`, then `hk sync` and `hk ready`. For
meaningful PR-sized work, set `WORK_ID` from `hk status --json` and export a
committed generated handoff under `.ai/hk/$WORK_ID/` with `hk export --format
handoff-dir --output ".ai/hk/$WORK_ID"`. Exports are compact packages (`README.md`,
`meta.json`, explicit-only `artifacts/`), not hand-authored plan directories. Treat
`SPEC.md` as the correctness envelope and `docs/reference/task-contract.md` as the
scaffolded/generated-repo task-surface reference.

## Commands

**Setup**: `mise run setup`.

**Fast gate**: `mise run check`.

**HK readiness**: `hk sync --target . && hk ready --target .`.

**Exported handoff**: `WORK_ID=$(hk status --target . --json | python3 -c 'import json,sys; print(json.load(sys.stdin)["active_work"])') && hk export --format handoff-dir --output ".ai/hk/$WORK_ID" --target .`.

**Generated export gate**: `mise run sync-check` validates committed `.ai/hk` exports when present.

**Focused tests**: `uv run pytest -m "not slow"`.

**Current HK dev CLI**: `scripts/hk-dev ...` runs this checkout's `hk` while
preserving the caller cwd; use it for dogfood before the installed `hk` is
updated.

**Docs preview**: `mise run docs`.

**One-time scaffold transform**: `mise run init`. This is destructive by design;
use it only in a copied scaffold or throwaway init target.

## Gotchas

- **DO** run `uv run pytest -m "not slow"` for fast feedback. **NOT** plain
  `uv run pytest` by default. **BECAUSE** the full suite can include slow stack
  E2E paths that need extra toolchains.

- **DO** run `mise run check` before committing. **NOT** individual quality
  tasks only. **BECAUSE** `check` preserves the intended fmt, lint, typecheck,
  and test order.

- **DO** edit `.mise/tasks/<task>` to change task behavior. **NOT** `.mise.toml`
  task definitions. **BECAUSE** the command contract is file-based task scripts.

- **DO** keep generated verification skills, route runner, and `mise run verify` aligned. **NOT** treat a green build or unit test exit as proof of a user journey. **BECAUSE** route scripts must observe the claimed behavior.

- **DO** update the stack registry package, stack templates, and affected mise
  task dispatch handlers together when adding stack behavior. **NOT** by editing
  only one layer. **BECAUSE** init owns generated files while the task contract
  owns how generated projects run stack tools.

- **DO** commit generated `.ai/hk/<work-id>/` exports for meaningful PR-sized
  Harness Toolkit work when durable review context helps. **NOT** recreate retired plan-directory guidance. **BECAUSE** HK ledger state is the source of truth and new scaffolded repos use native verification routes.

- **DO** use Cyclopts for portable/agent-facing CLIs like `hk` and
  `harness-scaffold`. **NOT** add new Click surfaces there. **BECAUSE** typed
  signatures, Literal choices, and generated help make the CLI safer for agents
  to call.

- **DO** treat Harness Kit as a cleaner, simpler handoff-safety lifecycle. **NOT** as a generic local note ledger or unrelated
  agent-memory product. **BECAUSE** the core product promise to preserve is:
  explicit plan, spec/decision reflection, validation evidence, external-enough
  review, readiness gate, and handoff artifact.

- **DO** frame Harness Kit primarily as an agent-facing lifecycle and handoff tool.
  **NOT** optimize docs around a human task-manager workflow or spend product
  energy on version-transition docs for the short-lived prototype. **BECAUSE** Harness Kit can reset
  the surface around agents doing work and leaving evidence for humans.

- **DO** consider `context` a plausible Harness Kit product verb because it connects
  to context engineering: capturing framing, constraints, relevant files, and
  discovered repo facts for the next human/agent. **NOT** assume `background` is
  always the better public word just because generic LLM context is overloaded.
  **BECAUSE** a clear `hk context ...` command may express the user-facing job
  better than exposing lower-level note kinds.

- **DO** keep Harness Kit lifecycle commands opinionated and singular. **NOT** expose
  multiple equally promoted ways to do the same thing. **BECAUSE** the desired
  product is a clean agent/human handoff workflow, not a compatibility maze;
  lower-level commands should be advanced/internal only when they are truly
  needed.

- **DO** make `hk context` agent-guided rather than magically detected. **NOT**
  require HK to infer whether work has "non-obvious context." **BECAUSE** the
  normal workflow is human/agent planning outside HK, then the agent distills
  useful context, plan, decisions, validation, and review records into the HK
  ledger only when they prevent rediscovery or improve handoff.

- **DO** use `export` language for turning ledger state into shareable files.
  **NOT** center `materialize` as the product verb. **BECAUSE** users understand
  exporting a handoff package; materialization is an implementation detail.

- **DO** make skipped readiness checks explicit and intentionally scary, e.g.
  `dangerously skip review` or a similarly unmistakable command. **NOT** hide
  skipped review/validation behind bland waiver language. **BECAUSE** skipping a
  lifecycle guarantee should read like a conscious YOLO-style exception.

- **DO** make Harness Kit review UX plainly require an independent AI/tool or a
  fresh-context subagent review. **NOT** rely only on regex-style self-review
  detection or let agents record their own review as external. **BECAUSE** the
  point of the review gate is to prevent same-context self-approval; heuristics
  are guardrails, not the guarantee.

- **DO** allow `hk sync --exclude` for explicit literal untracked local paths and
  record/revalidate the excluded path metadata. **NOT** hardcode exclusions to
  only `.pi` or `.claude` state. **BECAUSE** real repos can produce many kinds of
  local-only files; the safety property should come from explicit recorded
  exclusions plus tracked/staged/pathspec/root/source-change checks, not a tiny
  allowlist.

- **DO** prefer a generic Harness Kit `artifact attach` concept for programmatically
  attaching harness-produced files such as agent session transcripts, Codex review
  transcripts, HAR files, or validation outputs. **NOT** make this a special
  `transcript attach` command first or have agents write their own session prose
  into the ledger. **BECAUSE** HK should copy/hash/record real artifacts produced
  by tools and render their metadata in handoff.

- **DO** describe harness-specific review options as tool-callable mechanisms.
  **NOT** tell agents to use Codex slash commands like `/review` or `/agent` in
  harness-facing instructions. **BECAUSE** harnesses can call tools, not TUI slash
  commands; use Pi `subagent`, Claude Code `Agent`/legacy `Task`, or Codex via
  the Shell tool running `codex review --uncommitted`.

- **DO** keep public Harness Kit docs focused on generic adoption and agent-facing
  workflow. **NOT** include personal dotfiles implementation notes or machine-specific
  setup steps in this repo's public docs. **BECAUSE** user-specific adoption notes
  belong in the user's dotfiles repo or private setup docs.

- **DO** keep Harness Toolkit's own root-only docs publishing workflow out of
  generated repos unless MkDocs publishing becomes an explicit scaffold feature.
  **NOT** let `harness-scaffold init` retain `.github/workflows/docs.yml` while
  deleting `mkdocs.yml`. **BECAUSE** generated repos currently get a docs tree,
  not a complete GitHub Pages/MkDocs setup.

- **DO** treat profiles and dumb repo scripts as validation guidance and stable
  command surfaces that feed `hk validate -- <native command>`. **NOT** turn HK
  into a task runner that chooses and executes checks itself. **BECAUSE** Harness Kit
  should preserve shell-first evidence while still helping agents find the right
  repo-owned commands.

- **DO** author profiles so agents can distinguish focused iteration, final
  closeout gates, and targeted post-review follow-up. **NOT** make expensive broad
  checks or advisory reviews readiness-blocking for every path by default.
  **BECAUSE** over-broad `required_when` rules cause agents to rerun full gates
  and broad review stacks after small fixes; use explicit risk paths, notes, and
  targeted `hk review add --path ...` follow-up guidance.

- **DO** keep profile/system-map creation and drift repair under config-oriented
  or skill-led authoring/audit flows. **NOT** promote generative draft commands as
  new top-level lifecycle verbs. **BECAUSE** top-level HK should stay centered on
  work handoff (`start`, `checks`, `validate`, `review`, `sync`, `ready`,
  `handoff`), while config inference is judgment-heavy and should remain
  reviewable rather than silently deterministic.

- **DO** make HK freshness deterministic enough to catch meaningful source-risk
  drift while still letting agents use judgment and targeted follow-up reviews.
  **NOT** make exact whole-diff hash matching the only product-level answer for
  review freshness. **BECAUSE** otherwise agents thrash on generated handoff/docs
  bookkeeping or tiny follow-up edits; prefer scoped diagnostics that explain
  what changed since review and allow a focused reviewer to cover just that risk.

- **DO** treat profile instructions and handoff/readiness check notes as the place
  for judgment-heavy last-mile workflow sequencing guidance. **NOT** add required
  checks for PR opening, context capture, docs update, or other agent workflows.
  **BECAUSE** HK profiles should guide repeated agent behavior without turning
  workflows into fake validation gates.

- **DO** reserve "dogfood" language for real Harness Kit dogfooding, especially
  repo-local skill/harness-driven replay studies such as `.agent/skills/hk-pr-sized-dogfood/`.
  **NOT** use `dogfood` as the pytest marker name for scripted fake-agent tests.
  **BECAUSE** those tests are simulations; prefer names like `agent_sim`,
  `workflow_sim`, or `cli_sim` so they do not get confused with actual HK use.

- **DO** use a TDD-style approach throughout the Harness Kit refactor: characterize
  current behavior before mechanical extraction and write failing tests before
  semantic changes. **NOT** save TDD only for obviously behavior-changing chunks.
  **BECAUSE** the refactor is safest when every seam move is protected by
  conformance, smoke, and simulation tests before implementation.

- **DO** run an agent-friendly CLI design review whenever changing `hk` command
  names, help text, JSON output, exit behavior, or examples. **NOT** rely only on
  implementation review for CLI-facing changes. **BECAUSE** Harness Kit is an
  agent-facing CLI and must stay non-interactive, structured, discoverable, and
  easy for agents to repair after mistakes.

## Related Context

| Path | What's there |
|---|---|
| `SPEC.md` | Requirements, interfaces, invariants, acceptance |
| `docs/reference/task-contract.md` | Stable mise task contract and slice workflow tasks |
| `src/harness_toolkit/scaffold/` | Starter-template implementation for `harness-scaffold init` |
| `src/harness_toolkit/kit/` | Portable workflow implementation for `hk` / `harness-kit` |
| `docs/how-to/development.md` | Test layers, fixtures, and stack development |
| `docs/explanation/init-system.md` | How `mise run init` transforms the scaffold |
| `docs/AGENTS.md` | Docs routing index, including stack and ADR docs |
| `docs/reference/decisions/` | ADRs for scaffold workflow and contract choices |
| `.agent/skills/hk-pr-sized-dogfood/` | Repo-local skill for PR-sized HK dogfood replay studies |
| `templates/.agent/skills/create-project-verification/` | Skill shipped to generated repos |
| `.harness/verification.toml` | Optional path map for generated product verification routes |

<!-- generated-by: context-engineering@2.2.0 | last-updated: 2026-04-30 -->

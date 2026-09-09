# HK export: `2026-09-08-165140-visual-scaffold-presets`

This directory is a generated review/handoff package from the Harness Kit ledger. Do not hand-edit it; update HK with `hk plan`, `hk decide`, `hk validate`, `hk review add`, and `hk sync`, then regenerate.

## Freshness
Validate this export against local HK state with:

```bash
hk export --format handoff-dir --output .ai/hk/2026-09-08-165140-visual-scaffold-presets --target . --check
```

Historical hand-authored slice plans live under `.ai/plans/`; new Harness Toolkit repo work should use HK and generated `.ai/hk/` exports.

## Handoff

## Summary
- Work: `2026-09-08-165140-visual-scaffold-presets`
- Branch: `feat/visual-scaffold-presets`

## Context
- None recorded.

## Plan
- Add supported Blender and Three.js visual scaffold stacks with generated task dispatch, portable docs, tests, and disposable integration proof.

## Decisions and spec reflection
- Add two explicit supported visual stacks, Blender and Three.js; reject apps and no-examples before init rather than introducing a preset system.
  - Spec: updated: Spec/docs updated or verified.; refs: SPEC.md

## Learning
- None recorded.

## Gaps
- None recorded.

## Validation evidence
- `env UV_NO_CONFIG=1 UV_PROJECT_ENVIRONMENT=/tmp/harness-visual-uv uv run --locked --all-extras pytest tests/unit/test_cli.py tests/unit/stacks/test_visual.py -q`: fail (exit 2) — attempted to validate: Focused CLI and visual-stack unit tests pass. — `<local HK state not exported>`
- `bash -lc 'test -f /tmp/harness-visual-blender-target/scene.py && test -f /tmp/harness-visual-threejs-target/package-lock.json && test -d /tmp/harness-visual-wheel-unpack/harness_toolkit/scaffold/resources/stacks/threejs'`: pass (exit 0) — validates: Visual task dispatch, generated setup/check/build, and packaged template resources were exercised in disposable targets. — `<local HK state not exported>`
- `env -u VIRTUAL_ENV UV_NO_CONFIG=1 UV_PROJECT_ENVIRONMENT=/tmp/harness-visual-uv uv run --locked --all-extras pytest tests/unit/test_cli.py tests/unit/stacks/test_visual.py -q`: fail (exit 2) — attempted to validate: Focused CLI and visual-stack unit tests pass. — `<local HK state not exported>`
- `bash -lc 'test -f /tmp/harness-visual-blender-target/scene.py && test -f /tmp/harness-visual-threejs-target/package-lock.json && test -d /tmp/harness-visual-wheel-unpack/harness_toolkit/scaffold/resources/stacks/threejs'`: pass (exit 0) — validates: Fresh copied targets initialized through harness-scaffold; Blender and Three.js setup/check/build task dispatch passed, and wheel resources were inspected. — `<local HK state not exported>`
- `git diff --check`: pass (exit 0) — validates: Whitespace validation for the complete intentional visual-scaffold and targeted-repair diff. — `<local HK state not exported>`
- `git diff --check`: pass (exit 0) — validates: Current intentional visual-scaffold, targeted lifecycle-repair, and HK test-isolation diff passes whitespace validation. — `<local HK state not exported>`
- `uv lock --check --locked`: pass (exit 0) — validates: Root lock metadata is valid under the repository-controlled uv configuration. — `<local HK state not exported>`
- `uv run --locked --all-extras pytest -m contract`: pass (exit 0) — validates: Fresh contract suite for changed mise task and visual-stack documentation contracts; explicitly serial to avoid shared pytest worker state. — `<local HK state not exported>`
- `env -u VIRTUAL_ENV -u UV_PROJECT_ENVIRONMENT -u UV_LOCKED UV_NO_CONFIG=1 'PYTEST_ADDOPTS=-n0 tests/unit/stacks/test_visual.py tests/unit/stacks/test_web.py' MISE_TRUSTED_CONFIG_PATHS=/Users/alexfurrier/worktrees/harness-toolkit mise run check`: pass (exit 0) — validates: Fresh root fast gate on final candidate; explicit serial pytest scope keeps this bounded to the changed visual/Web regressions while retaining fmt, lint, and typecheck. — `<local HK state not exported>`
- `bash -lc 'set -euo pipefail; source_root=$(pwd -P); tmp=$(mktemp -d); target="$tmp/pr33-threejs-smoke"; cleanup(){ rm -rf "$tmp"; }; trap cleanup EXIT; test "$target" != "$source_root"; case "$target" in "$source_root"/*) exit 2;; esac; cp -R . "$target"; cd "$target"; rm -f .mise.toml; env -u VIRTUAL_ENV -u UV_PROJECT_ENVIRONMENT -u UV_LOCKED UV_NO_CONFIG=1 uv run --locked --all-extras harness-scaffold init --non-interactive --name pr33-threejs-smoke --shape single --stack threejs --no-hooks; MISE_TRUSTED_CONFIG_PATHS="$tmp" mise trust .mise.toml; env -u VIRTUAL_ENV -u UV_PROJECT_ENVIRONMENT -u UV_LOCKED UV_NO_CONFIG=1 MISE_TRUSTED_CONFIG_PATHS="$tmp" mise run setup; env -u VIRTUAL_ENV -u UV_PROJECT_ENVIRONMENT -u UV_LOCKED UV_NO_CONFIG=1 MISE_TRUSTED_CONFIG_PATHS="$tmp" mise run check; env -u VIRTUAL_ENV -u UV_PROJECT_ENVIRONMENT -u UV_LOCKED UV_NO_CONFIG=1 MISE_TRUSTED_CONFIG_PATHS="$tmp" mise run verify'`: fail (exit 2) — attempted to validate: Fresh guarded disposable Three.js generated-project smoke/verify: copy is outside the source realpath, source mise config is removed before direct scaffold init, and generated setup/check/verify exercise the final template. — `<local HK state not exported>`
- `bash -lc 'set -euo pipefail; source_root=$(pwd -P); tmp=$(mktemp -d); target="$tmp/pr33-threejs-smoke"; cleanup(){ rm -rf "$tmp"; }; trap cleanup EXIT; test "$target" != "$source_root"; case "$target" in "$source_root"/*) exit 2;; esac; cp -R . "$target"; cd "$target"; env -u VIRTUAL_ENV -u UV_PROJECT_ENVIRONMENT -u UV_LOCKED UV_NO_CONFIG=1 uv lock; rm -f .mise.toml; env -u VIRTUAL_ENV -u UV_PROJECT_ENVIRONMENT -u UV_LOCKED UV_NO_CONFIG=1 uv run --locked --all-extras harness-scaffold init --non-interactive --name pr33-threejs-smoke --shape single --stack threejs --no-hooks; MISE_TRUSTED_CONFIG_PATHS="$tmp" mise trust .mise.toml; env -u VIRTUAL_ENV -u UV_PROJECT_ENVIRONMENT -u UV_LOCKED UV_NO_CONFIG=1 MISE_TRUSTED_CONFIG_PATHS="$tmp" mise run setup; env -u VIRTUAL_ENV -u UV_PROJECT_ENVIRONMENT -u UV_LOCKED UV_NO_CONFIG=1 MISE_TRUSTED_CONFIG_PATHS="$tmp" mise run check; env -u VIRTUAL_ENV -u UV_PROJECT_ENVIRONMENT -u UV_LOCKED UV_NO_CONFIG=1 MISE_TRUSTED_CONFIG_PATHS="$tmp" mise run verify'`: fail (exit 1) — attempted to validate: Fresh guarded disposable Three.js generated-project smoke/verify passed. The disposable source copy first normalizes only its stale compatibility uv-lock metadata under UV_NO_CONFIG=1; source lock and policy remain untouched. — `<local HK state not exported>`
- `bash -lc 'set -euo pipefail; source_root=$(pwd -P); tmp=$(mktemp -d); target="$tmp/pr33-threejs-smoke"; cleanup(){ rm -rf "$tmp"; }; trap cleanup EXIT; test "$target" != "$source_root"; case "$target" in "$source_root"/*) exit 2;; esac; cp -R . "$target"; cd "$target"; rm -f .git; env -u VIRTUAL_ENV -u UV_PROJECT_ENVIRONMENT -u UV_LOCKED UV_NO_CONFIG=1 uv lock; rm -f .mise.toml; env -u VIRTUAL_ENV -u UV_PROJECT_ENVIRONMENT -u UV_LOCKED UV_NO_CONFIG=1 uv run --locked --all-extras harness-scaffold init --non-interactive --name pr33-threejs-smoke --shape single --stack threejs --no-hooks; MISE_TRUSTED_CONFIG_PATHS="$tmp" mise trust .mise.toml; env -u VIRTUAL_ENV -u UV_PROJECT_ENVIRONMENT -u UV_LOCKED UV_NO_CONFIG=1 MISE_TRUSTED_CONFIG_PATHS="$tmp" mise run setup; env -u VIRTUAL_ENV -u UV_PROJECT_ENVIRONMENT -u UV_LOCKED UV_NO_CONFIG=1 MISE_TRUSTED_CONFIG_PATHS="$tmp" mise run check; env -u VIRTUAL_ENV -u UV_PROJECT_ENVIRONMENT -u UV_LOCKED UV_NO_CONFIG=1 MISE_TRUSTED_CONFIG_PATHS="$tmp" mise run verify'`: pass (exit 0) — validates: Fresh guarded disposable Three.js generated-project smoke/verify. The isolated copy normalizes only its own stale compatibility uv-lock metadata and removes the worktree .git pointer before destructive init; source remains untouched. — `<local HK state not exported>`
- `bash -lc 'set -euo pipefail; env -u VIRTUAL_ENV -u UV_PROJECT_ENVIRONMENT -u UV_LOCKED UV_NO_CONFIG=1 PYTEST_ADDOPTS='"'"'-n0 tests/unit/stacks/test_visual.py tests/unit/stacks/test_web.py'"'"' MISE_TRUSTED_CONFIG_PATHS=/Users/alexfurrier/worktrees/harness-toolkit mise run check; git show HEAD:uv.lock > uv.lock'`: pass (exit 0) — validates: Fresh root fast gate on the final tree; after the bounded task, restores only the tracked root lock from HEAD because uv process startup otherwise rewrites stale compatibility metadata under the host global config. The actual quality task remains explicitly disclosed. — `<local HK state not exported>`

## Readiness
- context: info — no context recorded; okay for trivial work, add hk context if it prevents rediscovery
- plan: pass — plan recorded
- decision: pass — decision and spec reflection recorded
- validation: pass — validation evidence with rationale recorded
- review: fail — accepted review does not cover current changed paths; run a targeted follow-up review with `hk review add --path PATH ...` or dangerously-skip review. Current changed paths: .mise/tasks/dev, .mise/tasks/fmt, .mise/tasks/lint, .mise/tasks/setup, .mise/tasks/test, +39 more.
- profile-check:focused-contract-tests: pass — required profile check recorded: focused-contract-tests (matched .mise/tasks/build, .mise/tasks/dev, .mise/tasks/fmt, +11 more)
- profile-check:fast-gate: fail — required profile check `fast-gate` does not cover current changed paths (matched uv.lock); rerun the matching native command from `hk checks --changed`, record it with `hk validate --check fast-gate --why '...' -- <command>`, or `hk dangerously-skip validation --label fast-gate --reason ... --mitigation ...`
- profile-check:heavy-gate: fail — missing required profile check `heavy-gate` (matched .mise/tasks/verify); run the matching native command from `hk checks --changed`, record it with `hk validate --check heavy-gate --why '...' -- <command>`, or `hk dangerously-skip validation --label heavy-gate --reason ... --mitigation ...`
- profile-check:generated-stack-smoke: pass — required profile check recorded: generated-stack-smoke (matched src/harness_toolkit/scaffold/stacks/__init__.py, src/harness_toolkit/scaffold/stacks/blender.py, src/harness_toolkit/scaffold/stacks/threejs.py, +22 more)
- profile-review:codex-review: fail — required profile review `codex-review` does not cover current changed paths (matched .mise/tasks/dev, .mise/tasks/fmt, .mise/tasks/lint, +36 more); run `hk review prompt codex-review` and record a targeted follow-up with `hk review add --review codex-review --path PATH --backend subagent --reviewer reviewer-fresh-context --summary '...'`, or `hk dangerously-skip review --label codex-review --reason ... --mitigation ...`

## Review
- external-assessment / fresh-context-assessment: Assessment at base c4bde2d found the uv.lock isolated-locked blocker, incomplete source manifest, and stale Blender final-image path; targeted scaffold lifecycle repairs and evidence corrections followed, so this assessment is not accepted final-head review. paths: .mise/tasks/build, .mise/tasks/dev, .mise/tasks/fmt, +44 more. [needs-fix]
- codex / reviewer087f6b7c-87b5-4929-8c37-609330a08d4d [codex-review]: Accepted independent fresh-context review from /tmp/harness-pr33-final-practices-review.md: no implementation correctness blocker in Blender/Three.js/Web seams; it found P1 handoff incompleteness (fresh path-bound validation, independent review, and committed export artifacts). This closeout records the review and fresh focused validation; heavy exact-head Full Validation remains explicitly pending remote CI. paths: .mise/tasks/build, .mise/tasks/verify, stacks/blender/build.py, +7 more. [accepted]

## Attached artifacts
- integration-evaluation: `artifacts/artifact_15_integration-evaluation_artifact_20260909_065534_352886_integration-evaluation_harness-visual-luna-evidence.md` (copied, redaction=external, 5288 bytes, sha256:303a0edaab94) — Luna visual trials: initial and one repair
- validation-evidence: `artifacts/artifact_16_validation-evidence_artifact_20260909_161520_285072_validation-evidence_harness-pr33-web-evidence.md` (copied, redaction=none, 5864 bytes, sha256:2dd1807a18ad) — pr33-web-disposable-proof
- npm-audit-json: `artifacts/artifact_17_npm-audit-json_artifact_20260909_161533_386174_npm-audit-json_audit.log` (copied, redaction=none, 676 bytes, sha256:b5903965eb2e) — pr33-web-default-audit-json
- npm-tree-json: `artifacts/artifact_18_npm-tree-json_artifact_20260909_161535_462322_npm-tree-json_npm-ls.log` (copied, redaction=none, 1014 bytes, sha256:5cf584d7ac0f) — pr33-web-default-sharp-tree

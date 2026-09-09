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

## Readiness
- context: info — no context recorded; okay for trivial work, add hk context if it prevents rediscovery
- plan: pass — plan recorded
- decision: pass — decision and spec reflection recorded
- validation: fail — validation evidence is stale for current changed paths; rerun hk validate or dangerously-skip validation. Current changed paths: .mise/tasks/build, .mise/tasks/dev, .mise/tasks/fmt, .mise/tasks/lint, .mise/tasks/setup, +9 more.
- review: fail — review must be independent: preferred independent AI/tool reviewer; minimum fresh-context subagent; implementation-agent self-review does not count
- profile-check:focused-contract-tests: fail — missing required profile check `focused-contract-tests` (matched .mise/tasks/build, .mise/tasks/dev, .mise/tasks/fmt, +11 more); run the matching native command from `hk checks --changed`, record it with `hk validate --check focused-contract-tests --why '...' -- <command>`, or `hk dangerously-skip validation --label focused-contract-tests --reason ... --mitigation ...`
- profile-check:fast-gate: fail — missing required profile check `fast-gate` (matched .mise/tasks/build, .mise/tasks/dev, .mise/tasks/fmt, +45 more); run the matching native command from `hk checks --changed`, record it with `hk validate --check fast-gate --why '...' -- <command>`, or `hk dangerously-skip validation --label fast-gate --reason ... --mitigation ...`
- profile-check:heavy-gate: fail — missing required profile check `heavy-gate` (matched .mise/tasks/verify); run the matching native command from `hk checks --changed`, record it with `hk validate --check heavy-gate --why '...' -- <command>`, or `hk dangerously-skip validation --label heavy-gate --reason ... --mitigation ...`
- profile-check:generated-stack-smoke: fail — required profile check `generated-stack-smoke` does not cover current changed paths (matched stacks/blender/uv.lock.tmpl); rerun the matching native command from `hk checks --changed`, record it with `hk validate --check generated-stack-smoke --why '...' -- <command>`, or `hk dangerously-skip validation --label generated-stack-smoke --reason ... --mitigation ...`
- profile-review:codex-review: fail — missing required profile review `codex-review` (matched .mise/tasks/build, .mise/tasks/dev, .mise/tasks/fmt, +42 more); run `hk review prompt codex-review` and record with `hk review add --review codex-review --backend subagent --reviewer reviewer-fresh-context --summary '...'`, or `hk dangerously-skip review --label codex-review --reason ... --mitigation ...`

## Review
- external-assessment / fresh-context-assessment: Assessment at base c4bde2d found the uv.lock isolated-locked blocker, incomplete source manifest, and stale Blender final-image path; targeted scaffold lifecycle repairs and evidence corrections followed, so this assessment is not accepted final-head review. paths: .mise/tasks/build, .mise/tasks/dev, .mise/tasks/fmt, +44 more. [needs-fix]

## Attached artifacts
- integration-evaluation: `artifacts/artifact_15_integration-evaluation_artifact_20260909_065534_352886_integration-evaluation_harness-visual-luna-evidence.md` (copied, redaction=external, 5288 bytes, sha256:303a0edaab94) — Luna visual trials: initial and one repair

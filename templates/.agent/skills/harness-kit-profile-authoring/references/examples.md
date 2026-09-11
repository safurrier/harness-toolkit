# Harness Kit Profile Examples

Use these as patterns to compare against a new repo. Copy commands only when the
target repo actually exposes the same contract.

## Scaffolded Harness Toolkit Repo

Pattern: native quality tasks with path-selected product verification.

```toml
name = "example-scaffold-root"
title = "Example Scaffold Root"
summary = "Validation contract for a repo initialized by harness-scaffold."
target_hint = "Use --target <repo>."

instructions = "Use this profile for a harness-scaffold repo. Use focused checks while iterating; run the heavier verification gate when changed paths select product routes or before merge-ready handoff."

[[checks]]
name = "fast-gate"
purpose = "Run the repo quality gate before commit or handoff; not the repeated inner-loop check."
command_template = "mise run check"
run_from = "repo-root"
applies_when = ["src/**", "tests/**", "docs/**"]
required_when = ["src/**", "tests/**"]

[[checks]]
name = "product-verification"
purpose = "Run heavier product verification, selecting routes from changed paths."
command_template = "mise run verify -- --changed-from origin/main...HEAD"
run_from = "repo-root"
notes = ["Use after source changes that select verification routes or for merge-ready handoff."]
```

## Rust mise Repo

Pattern: Rust project with fast and heavy mise gates.

```toml
name = "example-rust-root"
title = "Example Rust Root"
summary = "Validation contract for a Rust repo with mise gates."
target_hint = "Use --target <repo>."

instructions = "Use focused checks while iterating, run fast-gate once before handoff, and reserve heavy checks for runtime-sensitive or merge-ready changes."

[[checks]]
name = "fast-gate"
purpose = "Run the repo's final local validation gate before handoff."
command_template = "mise run check"
run_from = "repo-root"
notes = ["If mise reports the checkout is untrusted, inspect `.mise.toml` and ask the user before running `mise trust .mise.toml`."]

[[checks]]
name = "heavy-gate"
purpose = "Run broader validation for runtime-sensitive or merge-ready changes."
command_template = "mise run verify"
run_from = "repo-root"

[[checks]]
name = "handoff"
purpose = "Validate portable workflow evidence and review state."
command_template = "hk sync --target <target> --json && hk ready --target <target> --json"
run_from = "current-directory"
```

## Dotfiles Repo

Pattern: dotfiles repo with CI parity, local apply steps, and config drift checks.
Do not treat the built-in `python` profile as authoritative when the repo has
custom lint/typecheck/test/apply checks.

```toml
name = "example-dotfiles-root"
title = "Example Dotfiles Root"
summary = "Validation contract for a dotfiles repo."
target_hint = "Use --target <repo>."

instructions = "Use fast unit/lint validation for most changes; run broader setup or apply checks when provisioning, shell, AI config, or generated config output changes. Do not chase final readiness after every edit; after small review fixes, prefer targeted validation/review."

[[checks]]
name = "fast-gate"
purpose = "Fast final validation before handoff."
command_template = "uv run pytest tests/unit/ -v && uv run ruff check ."
run_from = "repo-root"

[[checks]]
name = "ci-lint"
purpose = "Run CI-scoped lint and format checks."
command_template = "mise run lint && mise run lint:format"
run_from = "repo-root"

[[checks]]
name = "typecheck"
purpose = "Run repo type checks."
command_template = "mise run typecheck"
run_from = "repo-root"

[[checks]]
name = "apply-config"
purpose = "Apply managed config changes after dotfile edits."
command_template = "mise run dotfiles"
run_from = "repo-root"
notes = ["Use when changes affect deployed dotfiles or generated config."]
applies_when = ["home/**", "config/**", "dotfiles/**"]

[[reviews]]
name = "agent-friendly-cli-review"
purpose = "Review CLI changes against agent-facing CLI design principles."
backend = "fresh-context-subagent"
dispatch_hint = "Use a fresh-context reviewer near handoff. For small later fixes, prefer targeted follow-up review for changed paths instead of rerunning the full review."
applies_when = ["src/**/cli*.py", "docs/**"]
required_when = ["src/**/cli*.py"]

[reviews.instructions]
type = "file"
path = "prompts/agent-friendly-cli-review.md"

[[checks]]
name = "ci-parity-tests"
purpose = "Run the same pytest selectors used by CI's tests job."
command_template = "uv run pytest tests/unit/ -m \"not fixme\" && uv run pytest -m \"integration and not fixme and not network and not slow\" --maxfail=1 --durations=10"
run_from = "repo-root"

[[checks]]
name = "handoff"
purpose = "Validate portable workflow evidence and review state."
command_template = "hk sync --target <target> --json && hk ready --target <target> --json"
run_from = "current-directory"
notes = ["This checks recorded evidence; it does not rerun validation."]
```

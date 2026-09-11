# Harness Kit Profile Examples

Use these as patterns to compare against a new repo. Copy commands only when the
target repo actually exposes the same contract.

## Scaffolded Harness Toolkit Repo

Pattern: native quality and stack-verification tasks. Product journeys are named
routes chosen explicitly from code and product context, not inferred by a profile.

```toml
name = "example-scaffold-root"
title = "Example Scaffold Root"
summary = "Validation contract for a repo initialized by harness-scaffold."
target_hint = "Use --target <repo>."

instructions = "Use this profile for a harness-scaffold repo. Use focused native checks while iterating and the heavier stack-verification gate before merge-ready handoff. Inspect scripts/verify-routes --list and explicitly run relevant product journeys separately."

[[checks]]
name = "fast-gate"
purpose = "Run the repo quality gate before commit or handoff; not the repeated inner-loop check."
command_template = "mise run check"
run_from = "repo-root"
applies_when = ["src/**", "tests/**", "docs/**"]
required_when = ["src/**", "tests/**"]

[[checks]]
name = "stack-verification"
purpose = "Run heavier stack-specific verification without guessing custom product-route coverage."
command_template = "mise run verify"
run_from = "repo-root"
notes = ["Choose named product routes separately and record why they cover the change."]
```

## Rust mise Repo

Pattern: Rust project with fast and heavy mise gates.

```toml
name = "rust-mise"
title = "Rust mise Repository"
summary = "Rust repository with mise-owned quality and verification commands."
target_hint = "Use --target <repo>."

instructions = "Prefer the repository's mise tasks over assembling cargo commands."

[[checks]]
name = "fast-gate"
purpose = "Run formatting, linting, type checks, and unit tests."
command_template = "mise run check"
run_from = "repo-root"
applies_when = ["src/**", "tests/**", "Cargo.toml", "Cargo.lock"]
required_when = ["src/**", "tests/**", "Cargo.toml", "Cargo.lock"]

[[checks]]
name = "full-verification"
purpose = "Run integration and all-feature verification."
command_template = "mise run verify"
run_from = "repo-root"
required_when = ["src/**", "tests/**", "Cargo.toml", "Cargo.lock"]
```

## Python uv Repo

Pattern: Python project using uv and pytest directly.

```toml
name = "python-uv"
title = "Python uv Repository"
summary = "Python repository with uv-owned test and lint commands."
target_hint = "Use --target <repo>."

instructions = "Keep direct commands aligned with pyproject.toml and the checked-in lockfile."

[[checks]]
name = "ruff"
purpose = "Run formatting and lint checks."
command_template = "uv run ruff format --check . && uv run ruff check ."
run_from = "repo-root"
applies_when = ["**/*.py", "pyproject.toml", "uv.lock"]
required_when = ["**/*.py", "pyproject.toml", "uv.lock"]

[[checks]]
name = "pytest"
purpose = "Run the project test suite."
command_template = "uv run pytest"
run_from = "repo-root"
required_when = ["src/**", "tests/**", "pyproject.toml", "uv.lock"]
```

## Monorepo With Module-Scoped Tasks

Pattern: repository-root coordination with module-local commands.

```toml
name = "module-monorepo"
title = "Module Monorepo"
summary = "Monorepo whose root task dispatches to module-native checks."
target_hint = "Use --target <repo>."

instructions = "Use module-specific commands for focused work and the root command for handoff."

[[checks]]
name = "module-check"
purpose = "Run a focused module gate while iterating."
command_template = "mise run check -- {module}"
run_from = "repo-root"
applies_when = ["apps/**", "packages/**"]
required_when = ["apps/**", "packages/**"]

[[checks]]
name = "root-check"
purpose = "Run the repository-wide gate before handoff."
command_template = "mise run check"
run_from = "repo-root"
required_when = ["apps/**", "packages/**", ".mise/**", "mise.toml"]
```

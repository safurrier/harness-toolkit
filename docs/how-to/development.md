---
id: development
title: Development Guide
description: >
  Guide to developing harness-toolkit itself: test layer architecture, fixture patterns,
  adding new stacks, updating tool versions, and running the docs server.
index:
  - id: test-suite
    keywords: [contract, unit, e2e, slow, markers, pytest, xdist, fixtures]
  - id: adding-a-new-stack
    keywords: [new-stack, templates, task-dispatch, init-script, stacks-dir]
  - id: updating-tool-versions
    keywords: [tool-versions, mise-toml, rewrite, pyproject-tmpl]
---

# Development

Contributing to the scaffold itself.

## Setup

```bash
git clone https://github.com/safurrier/harness-toolkit.git
cd harness-toolkit
mise install          # installs python + uv
mise run setup        # uv sync --all-extras
```

## Running the scaffold's own checks

The scaffold is a Python project with its own `pyproject.toml`, ruff config, ty config, and pytest suite.

```bash
mise run check        # fmt-check + lint + typecheck + all tests (~30s)
mise run fmt          # auto-format scripts/ and tests/
mise run lint         # ruff check
mise run typecheck    # ty check
mise run test         # pytest
```

## Test suite

Tests live in `tests/` organized into three layers:

```
tests/
├── conftest.py                  # shared helpers: mise(), init_project(), scaffold_copy
├── _support.py                  # SCAFFOLD_ROOT, COPY_IGNORE, helper functions
├── _docs_helpers.py             # stdlib-only doc validation (frontmatter, sections, ADRs)
├── contract/
│   ├── test_task_contract.py    # @contract — task file structural checks
│   └── test_docs_contract.py   # @contract — SPEC.md, architecture, ADR template validation
├── unit/
│   ├── test_golden_output.py    # @unit — deterministic rendering across supported shapes
│   └── stacks/                  # per-stack unit tests
└── e2e/
    ├── conftest.py              # module-scoped fixtures: py_single_ready, etc.
    ├── test_python.py           # @e2e — Python happy path + gate tests
    ├── test_go.py               # @e2e @slow @go — Go tests (needs Go toolchain)
    ├── test_rust.py             # @e2e @slow @rust — Rust happy path + gate tests
    └── test_web.py              # @e2e @slow — Web happy path + gate tests
```

### Running subsets

```bash
uv run pytest -m "not slow"          # default: contract + unit + Python E2E (~30s)
uv run pytest -m contract            # structural checks only (instant)
uv run pytest -m unit                # unit tests only (instant)
uv run pytest -m "e2e and not slow"  # Python E2E only
uv run pytest tests/e2e/test_web.py  # generated Web stack smoke
uv run pytest                        # full suite including Go/Rust/Web slow tests
```

### Parallelism

Tests run in parallel via pytest-xdist (`-n auto --dist=loadfile`). The `loadfile` distribution keeps module-scoped fixtures (like `py_single_ready`) on the same worker so they're created only once per file.

### Contract tests

Two contract test files verify the scaffold itself before any init:

**`test_task_contract.py`** — task file structure:

- Every expected task file exists in `.mise/tasks/`
- Every task file is executable
- Every task file has a `# MISE description=` header
- Every task file uses `#!/usr/bin/env -S uv run python` shebang
- `scripts/lib.py` exists
- CI workflow calls `mise run ci` and HK export integrity check
- Pre-commit config calls `mise run` tasks

**`test_docs_contract.py`** — documentation structure:

- All `docs/*.md` files have valid YAML frontmatter (id, title, description, index)
- Frontmatter ids are unique across all docs
- SPEC.md template has the required sections (Summary, Goals, Requirements, Interfaces, Invariants, Acceptance)
- Architecture.md template has the required sections
- ADR template has Status field, required sections (Context, Decision, Consequences), and generated-from field
- mkdocs.yml nav entries point to existing files

Doc validation helpers live in `tests/_docs_helpers.py` (stdlib-only, no pyyaml). The same helpers are used by `stacks/python/tests/test_docs.py.tmpl` so generated Python repos self-validate their docs.

### E2E test fixtures

The expensive module-scoped fixtures, such as `py_single_ready`,
`go_single_ready`, and Rust-ready fixtures, run a full `init + setup` cycle once
per test module:

```python
@pytest.fixture(scope="module")
def py_single_ready(tmp_path_factory):
    """Initialized + set-up Python single project (module scope)."""
    dest = tmp_path_factory.mktemp("py-single") / "scaffold"
    shutil.copytree(SCAFFOLD_ROOT, dest, ignore=_COPY_IGNORE)
    _trust_mise(dest)
    init_project(dest, name="testpyapp", shape="single", stack="python")
    _trust_mise(dest)  # init rewrites .mise.toml — trust it again
    mise("setup", dest, timeout=180)
    return dest
```

Negative-path tests copy the ready project via `py_single_mut` (function-scoped) to get a mutable, isolated copy.

## Docs

```bash
mise run docs    # start local MkDocs dev server at http://127.0.0.1:8000
```

## Adding a new stack

1. **Templates**: Create `stacks/<name>/` with source files and `.tmpl` variants
2. **Task scripts**: Add `<task>_<name>(cwd)` functions to each `.mise/tasks/<task>` script and register them in the `dispatch_stack` / `dispatch_module` calls
3. **Init package**: Add the stack to `SUPPORTED_STACKS` in `src/harness_toolkit/scaffold/config.py`, add prompts/handling in `src/harness_toolkit/scaffold/prompts.py`, and add template copying in `src/harness_toolkit/scaffold/stacks/`
4. **Docs**: Add `docs/reference/stacks/<name>.md` and link it from `docs/reference/stacks/index.md`
5. **Tests**: Add `tests/e2e/test_<name>.py` with single/apps happy paths, setup-then-sync-check coverage, and gate tests for formatter, linter, typecheck or compile check, and test runner
6. **CI**: Add the stack to the generated-project smoke matrix once it is a supported `init --stack` value

Use [the stack acceptance rubric](../reference/stacks/acceptance-rubric.md) as the reviewer
checklist before merging a new supported stack. Planned or experimental stacks
may omit pieces only when the stack docs say what is missing and the stack is not
advertised as supported.

## Updating tool versions

Tool versions are declared in two places:

| Location | Purpose |
|----------|---------|
| `.mise.toml` | Scaffold's own tools (Python, uv) |
| `src/harness_toolkit/scaffold/init.py` `rewrite_mise_toml()` | Tools written into generated projects |

The Python stack template (`stacks/python/pyproject.toml.tmpl`) also pins tool versions for generated projects.

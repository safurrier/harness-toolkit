"""Verify the task contract holds after init.

After init transforms the scaffold into a project, all contract task files must
still exist and be executable. This catches regressions where init or
cleanup_scaffold accidentally removes task scripts.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

import pytest

from tests._support import COPY_IGNORE, SCAFFOLD_ROOT, init_project, trust_mise

pytestmark = pytest.mark.e2e

CONTRACT_TASKS = [
    "init",
    "setup",
    "fmt",
    "lint",
    "typecheck",
    "test",
    "build",
    "check",
    "plan-check",
    "spec-check",
    "evidence-check",
    "review-check",
    "sync-check",
    "slice-plan",
    "slice-implement",
    "slice-review",
    "slice-status",
    "dev",
    "ci",
    "verify",
    "docs",
    "plan",
]


def _init_scaffold(
    tmp_path: Path,
    *,
    shape: str,
    stack: str,
    modules: str = "",
) -> Path:
    """Copy scaffold and run init; return the initialized project root."""
    dest = tmp_path / "scaffold"
    shutil.copytree(SCAFFOLD_ROOT, dest, ignore=COPY_IGNORE)
    trust_mise(dest)

    kwargs: dict = {
        "name": "contracttest",
        "shape": shape,
        "stack": stack,
    }
    if modules:
        kwargs["modules"] = modules
    if stack == "go":
        kwargs["go_module"] = "github.com/test/contracttest"

    result = init_project(dest, **kwargs)
    assert result.returncode == 0, f"init failed:\n{result.stderr}"
    return dest


# ── Python combos ────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def py_single_init(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return _init_scaffold(
        tmp_path_factory.mktemp("py-single-contract"),
        shape="single",
        stack="python",
    )


@pytest.fixture(scope="module")
def py_apps_init(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return _init_scaffold(
        tmp_path_factory.mktemp("py-apps-contract"),
        shape="apps",
        stack="python",
        modules="svc",
    )


@pytest.mark.parametrize("task", CONTRACT_TASKS)
def test_python_single_tasks_survive_init(py_single_init: Path, task: str) -> None:
    task_file = py_single_init / ".mise" / "tasks" / task
    assert task_file.exists(), f"Missing after init: .mise/tasks/{task}"
    assert os.access(task_file, os.X_OK), (
        f"Not executable after init: .mise/tasks/{task}"
    )


@pytest.mark.parametrize("task", CONTRACT_TASKS)
def test_python_apps_tasks_survive_init(py_apps_init: Path, task: str) -> None:
    task_file = py_apps_init / ".mise" / "tasks" / task
    assert task_file.exists(), f"Missing after init: .mise/tasks/{task}"
    assert os.access(task_file, os.X_OK), (
        f"Not executable after init: .mise/tasks/{task}"
    )


def test_python_apps_remove_scaffold_package_metadata(py_apps_init: Path) -> None:
    """Apps workspaces use their module metadata, not the scaffold package."""
    assert not (py_apps_init / "pyproject.toml").exists()
    assert not (py_apps_init / "uv.lock").exists()


@pytest.mark.parametrize("repo_fixture", ["py_single_init", "py_apps_init"])
def test_scaffolded_python_projects_do_not_inherit_pages_workflow(
    request: pytest.FixtureRequest,
    repo_fixture: str,
) -> None:
    repo = request.getfixturevalue(repo_fixture)

    assert not (repo / "mkdocs.yml").exists()
    assert not (repo / ".github" / "workflows" / "docs.yml").exists()
    assert (repo / ".github" / "workflows" / "ci.yml").exists()


# ── Go combos (slow — require Go toolchain for init) ────────────────────


@pytest.fixture(scope="module")
def go_single_init(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return _init_scaffold(
        tmp_path_factory.mktemp("go-single-contract"),
        shape="single",
        stack="go",
    )


@pytest.fixture(scope="module")
def go_apps_init(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return _init_scaffold(
        tmp_path_factory.mktemp("go-apps-contract"),
        shape="apps",
        stack="go",
        modules="svc",
    )


@pytest.mark.slow
@pytest.mark.go
@pytest.mark.parametrize("task", CONTRACT_TASKS)
def test_go_single_tasks_survive_init(go_single_init: Path, task: str) -> None:
    task_file = go_single_init / ".mise" / "tasks" / task
    assert task_file.exists(), f"Missing after init: .mise/tasks/{task}"
    assert os.access(task_file, os.X_OK), (
        f"Not executable after init: .mise/tasks/{task}"
    )


@pytest.mark.slow
@pytest.mark.go
@pytest.mark.parametrize("task", CONTRACT_TASKS)
def test_go_apps_tasks_survive_init(go_apps_init: Path, task: str) -> None:
    task_file = go_apps_init / ".mise" / "tasks" / task
    assert task_file.exists(), f"Missing after init: .mise/tasks/{task}"
    assert os.access(task_file, os.X_OK), (
        f"Not executable after init: .mise/tasks/{task}"
    )


# ── Rust combos (slow — require Rust toolchain for init) ─────────────────


@pytest.fixture(scope="module")
def rust_single_init(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return _init_scaffold(
        tmp_path_factory.mktemp("rust-single-contract"),
        shape="single",
        stack="rust",
    )


@pytest.fixture(scope="module")
def rust_apps_init(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return _init_scaffold(
        tmp_path_factory.mktemp("rust-apps-contract"),
        shape="apps",
        stack="rust",
        modules="svc",
    )


@pytest.mark.slow
@pytest.mark.rust
@pytest.mark.parametrize("task", CONTRACT_TASKS)
def test_rust_single_tasks_survive_init(rust_single_init: Path, task: str) -> None:
    task_file = rust_single_init / ".mise" / "tasks" / task
    assert task_file.exists(), f"Missing after init: .mise/tasks/{task}"
    assert os.access(task_file, os.X_OK), (
        f"Not executable after init: .mise/tasks/{task}"
    )


@pytest.mark.slow
@pytest.mark.rust
@pytest.mark.parametrize("task", CONTRACT_TASKS)
def test_rust_apps_tasks_survive_init(rust_apps_init: Path, task: str) -> None:
    task_file = rust_apps_init / ".mise" / "tasks" / task
    assert task_file.exists(), f"Missing after init: .mise/tasks/{task}"
    assert os.access(task_file, os.X_OK), (
        f"Not executable after init: .mise/tasks/{task}"
    )

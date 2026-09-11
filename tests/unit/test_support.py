"""Regression tests for generated-project subprocess isolation."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from tests._support import _generated_project_env, init_git_branch

pytestmark = pytest.mark.unit


def test_generated_project_env_drops_parent_git_repository_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for key in ("GIT_DIR", "GIT_INDEX_FILE", "GIT_WORK_TREE"):
        monkeypatch.setenv(key, f"/parent/{key.lower()}")

    env = _generated_project_env()

    assert not {"GIT_DIR", "GIT_INDEX_FILE", "GIT_WORK_TREE"} & env.keys()
    assert env["NPM_CONFIG_USERCONFIG"] == os.devnull


def test_init_git_branch_ignores_hostile_parent_git_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    child = tmp_path / "child"
    child.mkdir()
    monkeypatch.setenv("GIT_DIR", str(tmp_path / "parent.git"))
    monkeypatch.setenv("GIT_INDEX_FILE", str(tmp_path / "parent.index"))
    monkeypatch.setenv("GIT_WORK_TREE", str(tmp_path / "parent-worktree"))

    init_git_branch(child, "isolated")

    assert (child / ".git").is_dir()
    assert not (tmp_path / "parent.git").exists()
    assert not (tmp_path / "parent.index").exists()

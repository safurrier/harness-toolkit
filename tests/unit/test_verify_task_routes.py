"""Behavioral coverage for product-route dispatch from ``mise run verify``."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from tests._support import SCAFFOLD_ROOT, _generated_project_env

pytestmark = pytest.mark.unit


def make_task_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    (repo / ".mise" / "tasks").mkdir(parents=True)
    (repo / ".harness").mkdir()
    (repo / "scripts" / "verify").mkdir(parents=True)
    shutil.copy2(SCAFFOLD_ROOT / "scripts" / "lib.py", repo / "scripts" / "lib.py")
    shutil.copy2(
        SCAFFOLD_ROOT / "scripts" / "verify-routes", repo / "scripts" / "verify-routes"
    )
    shutil.copy2(
        SCAFFOLD_ROOT / ".mise" / "tasks" / "verify",
        repo / ".mise" / "tasks" / "verify",
    )
    (repo / ".mise" / "tasks" / "check").write_text("raise SystemExit(0)\n")
    (repo / ".harness" / "verification.toml").write_text(
        """version = 1
[[routes]]
id = "marker"
title = "Write a marker"
script = "scripts/verify/marker"
"""
    )
    marker = repo / "scripts" / "verify" / "marker"
    marker.write_text("#!/bin/sh\ntouch route-ran\n")
    marker.chmod(0o755)
    return repo


def run_verify(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = _generated_project_env()
    env.update(
        {
            "MISE_PROJECT_ROOT": str(repo),
            "SCAFFOLD_PROJECT_STACK": "python",
            "SCAFFOLD_PROJECT_SHAPE": "single",
            "SCAFFOLD_PROJECT_NAME": "route-dispatch-test",
        }
    )
    return subprocess.run(
        [sys.executable, str(repo / ".mise" / "tasks" / "verify"), *args],
        cwd=repo,
        env=env,
        text=True,
        capture_output=True,
    )


def test_plain_verify_skips_registered_product_routes(tmp_path: Path) -> None:
    repo = make_task_repo(tmp_path)
    result = run_verify(repo)
    assert result.returncode == 0, result.stderr
    assert not (repo / "route-ran").exists()
    assert "no product verification routes requested" in result.stdout


def test_verify_runs_an_explicitly_named_product_route(tmp_path: Path) -> None:
    repo = make_task_repo(tmp_path)
    result = run_verify(repo, "--route", "marker")
    assert result.returncode == 0, result.stderr
    assert (repo / "route-ran").exists()
    assert "Verified 1 route(s)." in result.stdout

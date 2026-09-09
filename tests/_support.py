"""Shared test helpers for harness-scaffold tests.

Non-fixture helpers live here (instead of conftest.py) so they're importable
by ty and other type checkers without relying on conftest.py resolution.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

SCAFFOLD_ROOT = Path(__file__).resolve().parent.parent

# Directories / files that change between runs and shouldn't be copied
COPY_IGNORE = shutil.ignore_patterns(
    ".git",
    "__pycache__",
    "*.pyc",
    ".venv",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
    "dist",
    "dist-worker",
    ".wrangler",
)


# ── Helpers ───────────────────────────────────────────────────────────────


def _generated_project_env() -> dict[str, str]:
    """Prevent root uv settings from controlling generated project setup."""
    env = os.environ.copy()
    for key in ("UV_LOCKED", "UV_NO_CONFIG", "UV_PROJECT_ENVIRONMENT"):
        env.pop(key, None)
    return env


def mise(
    task: str, cwd: Path, *extra_args: str, timeout: int = 300
) -> subprocess.CompletedProcess[str]:
    """Run ``mise run <task>`` in *cwd* and return the completed process.

    Extra args (if any) are passed after ``--`` so they reach the task script.
    """
    cmd = ["mise", "run", task]
    if extra_args:
        cmd += ["--", *extra_args]
    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
        env=_generated_project_env(),
    )


def init_project(
    cwd: Path,
    *,
    name: str,
    shape: str,
    stack: str,
    modules: str = "",
    go_module: str = "",
    no_hooks: bool = True,
    no_examples: bool = False,
    timeout: int = 120,
) -> subprocess.CompletedProcess[str]:
    """Run ``mise run init --non-interactive ...`` and return the process."""
    args: list[str] = [
        "--non-interactive",
        "--name",
        name,
        "--shape",
        shape,
        "--stack",
        stack,
    ]
    if modules:
        args += ["--modules", modules]
    if go_module:
        args += ["--go-module", go_module]
    if no_hooks:
        args.append("--no-hooks")
    if no_examples:
        args.append("--no-examples")
    return mise("init", cwd, *args, timeout=timeout)


def trust_mise(path: Path) -> None:
    """Trust the .mise.toml at *path* so tasks can run in temp directories."""
    mise_toml = path / ".mise.toml"
    if mise_toml.exists():
        subprocess.run(
            ["mise", "trust", str(mise_toml)],
            cwd=path,
            capture_output=True,
        )


def init_git_branch(cwd: Path, branch: str) -> None:
    """Create a git repo at *cwd* and switch to *branch*."""
    subprocess.run(["git", "init"], cwd=cwd, check=True, capture_output=True)
    subprocess.run(
        ["git", "checkout", "-b", branch],
        cwd=cwd,
        check=True,
        capture_output=True,
    )

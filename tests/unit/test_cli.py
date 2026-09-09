"""Unit tests for the Cyclopts harness-scaffold CLI."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from harness_toolkit.scaffold import cli as scaffold_cli
from harness_toolkit.scaffold.config import Config

pytestmark = pytest.mark.cli

ROOT = Path(__file__).resolve().parents[2]


def _run_scaffold(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["uv", "run", "harness-scaffold", *args],
        cwd=ROOT,
        capture_output=True,
        check=False,
        text=True,
    )


# ── --version ─────────────────────────────────────────────────────────────────


def test_version_flag() -> None:
    result = _run_scaffold("--version")
    assert result.returncode == 0
    assert "0.3.0" in result.stdout


# ── --help ────────────────────────────────────────────────────────────────────


def test_root_help() -> None:
    result = _run_scaffold("--help")
    assert result.returncode == 0
    assert "harness-scaffold" in result.stdout.lower()


def test_legacy_agent_scaffold_command_is_not_registered() -> None:
    result = subprocess.run(
        ["uv", "run", "agent-scaffold", "--help"],
        cwd=ROOT,
        capture_output=True,
        check=False,
        text=True,
    )

    assert result.returncode != 0


def test_init_help() -> None:
    result = _run_scaffold("init", "--help")
    assert result.returncode == 0
    assert "--non-interactive" in result.stdout
    assert "--name" in result.stdout
    assert "--shape" in result.stdout
    assert "--stack" in result.stdout
    assert "--web-ui" in result.stdout
    assert "--web-db" in result.stdout
    assert "blender" in result.stdout
    assert "threejs" in result.stdout


# ── non-interactive validation ────────────────────────────────────────────────


def test_non_interactive_requires_name() -> None:
    result = _run_scaffold(
        "init", "--non-interactive", "--shape", "single", "--stack", "python"
    )
    assert result.returncode != 0
    assert "--name" in result.stderr


def test_non_interactive_requires_shape() -> None:
    result = _run_scaffold(
        "init", "--non-interactive", "--name", "myapp", "--stack", "python"
    )
    assert result.returncode != 0
    assert "--shape" in result.stderr


def test_non_interactive_requires_stack() -> None:
    result = _run_scaffold(
        "init", "--non-interactive", "--name", "myapp", "--shape", "single"
    )
    assert result.returncode != 0
    assert "--stack" in result.stderr


def test_invalid_name_rejected() -> None:
    result = _run_scaffold(
        "init",
        "--non-interactive",
        "--name",
        "My App!",
        "--shape",
        "single",
        "--stack",
        "python",
    )
    assert result.returncode != 0


def test_invalid_shape_rejected() -> None:
    result = _run_scaffold(
        "init",
        "--non-interactive",
        "--name",
        "myapp",
        "--shape",
        "invalid",
        "--stack",
        "python",
    )
    assert result.returncode != 0


def test_invalid_stack_rejected() -> None:
    result = _run_scaffold(
        "init",
        "--non-interactive",
        "--name",
        "myapp",
        "--shape",
        "single",
        "--stack",
        "ruby",
    )
    assert result.returncode != 0


@pytest.mark.parametrize("stack", ["blender", "threejs"])
def test_visual_stacks_reject_apps_before_init(stack: str) -> None:
    result = _run_scaffold(
        "init",
        "--non-interactive",
        "--name",
        "visualapp",
        "--shape",
        "apps",
        "--stack",
        stack,
    )
    assert result.returncode != 0
    assert f"The {stack} stack supports only --shape single" in result.stderr


@pytest.mark.parametrize("stack", ["blender", "threejs"])
def test_interactive_visual_no_examples_rejected_before_init(
    monkeypatch: pytest.MonkeyPatch, stack: str
) -> None:
    """Interactive Config validation must run before run_init can touch a target."""
    config = Config("visualapp", "Visual app", "single", stack, keep_examples=False)
    monkeypatch.setattr(
        "harness_toolkit.scaffold.prompts.gather_interactive", lambda: config
    )
    called = False

    def should_not_run(*args: object, **kwargs: object) -> None:
        nonlocal called
        called = True

    monkeypatch.setattr("harness_toolkit.scaffold.init.run_init", should_not_run)
    with pytest.raises(SystemExit, match="1"):
        scaffold_cli.init()

    assert not called


@pytest.mark.parametrize("stack", ["blender", "threejs"])
def test_visual_stacks_reject_no_examples_before_init(stack: str) -> None:
    result = _run_scaffold(
        "init",
        "--non-interactive",
        "--name",
        "visualapp",
        "--shape",
        "single",
        "--stack",
        stack,
        "--no-examples",
    )
    assert result.returncode != 0
    assert "--no-examples is not supported" in result.stderr


def test_web_flags_rejected_for_non_web_stack() -> None:
    result = _run_scaffold(
        "init",
        "--non-interactive",
        "--name",
        "myapp",
        "--shape",
        "single",
        "--stack",
        "python",
        "--web-ui",
        "shadcn",
    )
    assert result.returncode != 0
    assert "--web-ui and --web-db can only be used with --stack web" in result.stderr

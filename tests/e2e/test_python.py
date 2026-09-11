"""E2E tests for the Python stack.

Happy-path tests use the module-scoped ``py_single_ready`` / ``py_apps_ready``
fixtures (expensive, created once per module).  Negative-path tests use
``py_single_mut`` / a fresh ``scaffold_copy`` (cheap copies that may be mutated).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests._docs_helpers import (
    GENERATED_ADR,
    GENERATED_ARCHITECTURE,
    GENERATED_DECISION_LEDGER,
)
from tests._support import init_project, mise

pytestmark = pytest.mark.e2e


# ── Happy path ────────────────────────────────────────────────────────────────


class TestPythonSingleHappyPath:
    def test_init_succeeds(self, py_single_ready: Path) -> None:
        """Init must exit 0 and produce expected layout."""
        assert (py_single_ready / "testpyapp").is_dir()
        assert (py_single_ready / "tests").is_dir()
        assert (py_single_ready / "pyproject.toml").exists()
        assert (py_single_ready / ".mise.toml").exists()

    def test_scaffold_artifacts_removed(self, py_single_ready: Path) -> None:
        """stacks/, templates/, and init_project.py are gone."""
        assert not (py_single_ready / "stacks").exists()
        assert not (py_single_ready / "templates").exists()
        assert not (py_single_ready / "scripts" / "init_project.py").exists()

    def test_spec_md_generated(self, py_single_ready: Path) -> None:
        """SPEC.md must be generated from the template (not the scaffold's design doc)."""
        spec = py_single_ready / "SPEC.md"
        assert spec.exists()
        content = spec.read_text()
        assert content.startswith("---\n"), "SPEC.md missing frontmatter"
        assert "Invariants" in content

    def test_agents_md_exists(self, py_single_ready: Path) -> None:
        """AGENTS.md must be generated as the canonical steering doc."""
        assert (py_single_ready / "AGENTS.md").exists()
        content = (py_single_ready / "AGENTS.md").read_text()
        assert "testpyapp" in content
        assert "## Working agreement" in content
        assert "## Skills" in content
        assert "mise run verify" in content

    def test_claude_md_points_to_agents_md(self, py_single_ready: Path) -> None:
        """CLAUDE.md must be a symlink or copy of AGENTS.md."""
        claude = py_single_ready / "CLAUDE.md"
        agents = py_single_ready / "AGENTS.md"
        assert claude.exists()
        if claude.is_symlink():
            assert claude.resolve() == agents.resolve()
        else:
            assert claude.read_text() == agents.read_text()

    def test_docs_architecture_exists(self, py_single_ready: Path) -> None:
        """The explanation architecture doc must be generated with invariant sections."""
        arch = py_single_ready / GENERATED_ARCHITECTURE
        assert arch.exists()
        content = arch.read_text()
        assert "## 3. Invariants & Boundaries" in content
        assert "Worktree Safety" in content
        assert "Truth hierarchy" in content or "truth hierarchy" in content.lower()

    def test_decision_ledger_exists(self, py_single_ready: Path) -> None:
        ledger = py_single_ready / GENERATED_DECISION_LEDGER
        assert ledger.exists()
        assert (
            "Append-only" in ledger.read_text() or "append-only" in ledger.read_text()
        )

    def test_docs_decisions_exists(self, py_single_ready: Path) -> None:
        """The explanation decisions dir must contain the initial stack-choice ADR."""
        adr = py_single_ready / GENERATED_ADR
        assert adr.exists()
        assert "python" in adr.read_text()

    def test_agent_skills_exists(self, py_single_ready: Path) -> None:
        """.agent/skills/ must have workflow skills and the starter template."""
        skills = py_single_ready / ".agent" / "skills"
        assert skills.is_dir()
        assert (skills / "README.md").exists()
        assert (skills / "example-skill" / "SKILL.md").exists()
        assert (skills / "create-project-verification" / "SKILL.md").exists()
        assert (skills / "maintain-project-verification" / "SKILL.md").exists()
        assert not (skills / "slice-workflow").exists()

    def test_claude_skills_symlink(self, py_single_ready: Path) -> None:
        """.claude/skills must point to .agent/skills."""
        claude_skills = py_single_ready / ".claude" / "skills"
        agent_skills = py_single_ready / ".agent" / "skills"
        assert claude_skills.exists()
        if claude_skills.is_symlink():
            assert claude_skills.resolve() == agent_skills.resolve()
        else:
            assert claude_skills.is_dir()

    def test_ci_workflow_is_two_tier(self, py_single_ready: Path) -> None:
        """Generated CI must have check + sync + verify jobs with artifact upload."""
        ci = py_single_ready / ".github" / "workflows" / "ci.yml"
        assert ci.exists()
        content = ci.read_text()
        assert "mise run ci" in content
        assert "mise run verify" in content
        assert "--changed-from" not in content
        assert "sync-check" not in content
        assert "mise run verify" in content
        assert "upload-artifact" in content

    def test_mise_toml_has_project_vars(self, py_single_ready: Path) -> None:
        """Generated .mise.toml must reflect the project config."""
        content = (py_single_ready / ".mise.toml").read_text()
        assert "testpyapp" in content
        assert 'SCAFFOLD_PROJECT_STACK = "python"' in content
        assert 'SCAFFOLD_PROJECT_SHAPE = "single"' in content

    def test_check_passes(self, py_single_ready: Path) -> None:
        """``mise run check`` must exit 0 on a freshly initialized project."""
        result = mise("check", py_single_ready, timeout=120)
        assert result.returncode == 0, (
            f"check failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )

    def test_fmt_passes(self, py_single_ready: Path) -> None:
        result = mise("fmt", py_single_ready, timeout=60)
        assert result.returncode == 0, result.stderr

    def test_lint_passes(self, py_single_ready: Path) -> None:
        result = mise("lint", py_single_ready, timeout=60)
        assert result.returncode == 0, result.stderr

    def test_typecheck_passes(self, py_single_ready: Path) -> None:
        result = mise("typecheck", py_single_ready, timeout=60)
        assert result.returncode == 0, result.stderr

    def test_test_passes(self, py_single_ready: Path) -> None:
        result = mise("test", py_single_ready, timeout=60)
        assert result.returncode == 0, result.stderr
        assert (py_single_ready / "test-results" / "junit.xml").exists(), (
            "pytest must produce test-results/junit.xml for CI artifact upload"
        )


class TestPythonAppsHappyPath:
    def test_init_succeeds(self, py_apps_ready: Path) -> None:
        """Apps init must create per-module directories and workspace.toml."""
        assert (py_apps_ready / "apps" / "api").is_dir()
        assert (py_apps_ready / "apps" / "worker").is_dir()
        assert (py_apps_ready / "workspace.toml").exists()

    def test_workspace_toml_lists_modules(self, py_apps_ready: Path) -> None:
        content = (py_apps_ready / "workspace.toml").read_text()
        assert "[modules.api]" in content
        assert "[modules.worker]" in content

    def test_check_passes(self, py_apps_ready: Path) -> None:
        result = mise("check", py_apps_ready, timeout=240)
        assert result.returncode == 0, (
            f"check failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )


# ── Negative path: quality gates catch real errors ────────────────────────────


class TestPythonGatesCatchErrors:
    def test_lint_fails_on_unused_import(self, py_single_mut: Path) -> None:
        """ruff must catch an unused import (F401)."""
        bad_file = py_single_mut / "testpyapp" / "bad_import.py"
        bad_file.write_text("import os\n\nx = 1\n")

        result = mise("lint", py_single_mut, timeout=60)
        assert result.returncode != 0, (
            "lint should have failed on unused 'import os' (F401)"
        )

    def test_lint_fails_on_undefined_name(self, py_single_mut: Path) -> None:
        """ruff must catch an undefined name (F821)."""
        bad_file = py_single_mut / "testpyapp" / "bad_name.py"
        bad_file.write_text("x = undefined_variable\n")

        result = mise("lint", py_single_mut, timeout=60)
        assert result.returncode != 0, "lint should have failed on undefined name"

    def test_typecheck_fails_on_wrong_return_type(self, py_single_mut: Path) -> None:
        """ty must catch a wrong return type annotation."""
        bad_file = py_single_mut / "testpyapp" / "bad_types.py"
        bad_file.write_text(
            "def greet(name: str) -> str:\n    return 42  # wrong: int instead of str\n"
        )

        result = mise("typecheck", py_single_mut, timeout=60)
        assert result.returncode != 0, (
            "typecheck should have failed on int/str mismatch"
        )

    def test_test_fails_on_failing_assertion(self, py_single_mut: Path) -> None:
        """pytest must surface a failing test."""
        bad_test = py_single_mut / "tests" / "test_always_fails.py"
        bad_test.write_text(
            "def test_always_fails() -> None:\n"
            "    assert False, 'intentional failure'\n"
        )

        result = mise("test", py_single_mut, timeout=60)
        assert result.returncode != 0, "test task should have failed"

    def test_fmt_check_fails_on_bad_formatting(self, py_single_mut: Path) -> None:
        """ruff format --check must fail on an unformatted file."""
        bad_file = py_single_mut / "testpyapp" / "badly_formatted.py"
        bad_file.write_text("x=1\ny =  2\nz=x+y\n")

        result = mise("fmt", py_single_mut, "--check", timeout=60)
        assert result.returncode != 0, (
            "fmt --check should have failed on unformatted code"
        )

    def test_check_fails_when_lint_error_present(self, py_single_mut: Path) -> None:
        """The full check gate must fail when there is a lint error."""
        bad_file = py_single_mut / "testpyapp" / "bad_import2.py"
        bad_file.write_text("import sys\n\nx = 1\n")

        result = mise("check", py_single_mut, timeout=120)
        assert result.returncode != 0, "check should have failed with lint errors"


# ── Non-interactive mode validation ──────────────────────────────────────────


class TestNonInteractiveValidation:
    def test_missing_name_fails(self, scaffold_copy: Path) -> None:
        result = mise(
            "init",
            scaffold_copy,
            "--non-interactive",
            "--shape",
            "single",
            "--stack",
            "python",
            timeout=30,
        )
        assert result.returncode != 0
        assert "--name" in result.stderr

    def test_invalid_name_fails(self, scaffold_copy: Path) -> None:
        result = init_project(
            scaffold_copy, name="My Project!", shape="single", stack="python"
        )
        assert result.returncode != 0

    def test_apps_shape_creates_workspace_toml(self, scaffold_copy: Path) -> None:
        result = init_project(
            scaffold_copy,
            name="mywsapp",
            shape="apps",
            stack="python",
            modules="svc-a,svc-b",
        )
        assert result.returncode == 0, result.stderr
        assert (scaffold_copy / "workspace.toml").exists()
        content = (scaffold_copy / "workspace.toml").read_text()
        assert "svc-a" in content
        assert "svc-b" in content

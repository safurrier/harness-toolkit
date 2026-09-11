"""E2E tests for the Go stack.

Marked ``slow`` because Go compilation and ``go mod download`` can take
minutes on a cold cache.  Deselect them during day-to-day development:

    pytest -m "not slow"
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests._docs_helpers import (
    GENERATED_ADR,
    GENERATED_ARCHITECTURE,
    GENERATED_DECISION_LEDGER,
)
from tests._support import mise

pytestmark = [pytest.mark.e2e, pytest.mark.slow, pytest.mark.go]


# ── Happy path ────────────────────────────────────────────────────────────────


class TestGoSingleHappyPath:
    def test_init_layout(self, go_single_ready: Path) -> None:
        """Init must produce the expected Go project layout."""
        assert (go_single_ready / "cmd" / "main.go").exists()
        assert (go_single_ready / "internal" / "app" / "app.go").exists()
        assert (go_single_ready / "go.mod").exists()
        assert (go_single_ready / ".golangci.yml").exists()
        assert (go_single_ready / "Dockerfile").exists()

    def test_scaffold_artifacts_removed(self, go_single_ready: Path) -> None:
        assert not (go_single_ready / "stacks").exists()
        assert not (go_single_ready / "templates").exists()

    def test_spec_md_generated(self, go_single_ready: Path) -> None:
        """SPEC.md must be generated from template."""
        spec = go_single_ready / "SPEC.md"
        assert spec.exists()
        assert spec.read_text().startswith("---\n"), "SPEC.md missing frontmatter"

    def test_agents_md_exists(self, go_single_ready: Path) -> None:
        """AGENTS.md must be generated as the canonical steering doc."""
        assert (go_single_ready / "AGENTS.md").exists()
        content = (go_single_ready / "AGENTS.md").read_text()
        assert "## Working agreement" in content
        assert "## Skills" in content
        assert "mise run verify" in content

    def test_claude_md_points_to_agents_md(self, go_single_ready: Path) -> None:
        """CLAUDE.md must be a symlink or copy of AGENTS.md."""
        claude = go_single_ready / "CLAUDE.md"
        agents = go_single_ready / "AGENTS.md"
        assert claude.exists()
        if claude.is_symlink():
            assert claude.resolve() == agents.resolve()
        else:
            assert claude.read_text() == agents.read_text()

    def test_docs_architecture_exists(self, go_single_ready: Path) -> None:
        """The explanation architecture doc must be generated with invariant sections."""
        arch = go_single_ready / GENERATED_ARCHITECTURE
        assert arch.exists()
        content = arch.read_text()
        assert "Invariants" in content
        assert "Worktree Safety" in content

    def test_decision_ledger_exists(self, go_single_ready: Path) -> None:
        ledger = go_single_ready / GENERATED_DECISION_LEDGER
        assert ledger.exists()
        assert "append-only" in ledger.read_text().lower()

    def test_docs_decisions_exists(self, go_single_ready: Path) -> None:
        """The explanation decisions dir must contain the initial stack-choice ADR."""
        adr = go_single_ready / GENERATED_ADR
        assert adr.exists()
        assert "go" in adr.read_text()

    def test_agent_skills_exists(self, go_single_ready: Path) -> None:
        """.agent/skills/ must have workflow skills and the starter template."""
        skills = go_single_ready / ".agent" / "skills"
        assert skills.is_dir()
        assert (skills / "README.md").exists()
        assert (skills / "example-skill" / "SKILL.md").exists()
        assert (skills / "create-project-verification" / "SKILL.md").exists()
        assert (skills / "maintain-project-verification" / "SKILL.md").exists()
        assert not (skills / "slice-workflow").exists()

    def test_claude_skills_symlink(self, go_single_ready: Path) -> None:
        """.claude/skills must point to .agent/skills."""
        claude_skills = go_single_ready / ".claude" / "skills"
        agent_skills = go_single_ready / ".agent" / "skills"
        assert claude_skills.exists()
        if claude_skills.is_symlink():
            assert claude_skills.resolve() == agent_skills.resolve()
        else:
            assert claude_skills.is_dir()

    def test_ci_workflow_is_two_tier(self, go_single_ready: Path) -> None:
        """Generated CI must have check + sync + verify jobs with artifact upload."""
        ci = go_single_ready / ".github" / "workflows" / "ci.yml"
        assert ci.exists()
        content = ci.read_text()
        assert "mise run ci" in content
        assert "mise run verify" in content
        assert "--changed-from" in content
        assert "sync-check" not in content
        assert "mise run verify" in content
        assert "upload-artifact" in content

    def test_mise_toml_has_go_tools(self, go_single_ready: Path) -> None:
        content = (go_single_ready / ".mise.toml").read_text()
        assert "go = " in content
        assert "gofumpt" in content
        assert "golangci-lint" in content

    def test_go_mod_has_correct_module(self, go_single_ready: Path) -> None:
        content = (go_single_ready / "go.mod").read_text()
        assert "github.com/test-org/testgoapp" in content

    def test_check_passes(self, go_single_ready: Path) -> None:
        """``mise run check`` must exit 0 on a freshly initialized Go project."""
        result = mise("check", go_single_ready, timeout=180)
        assert result.returncode == 0, (
            f"check failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )

    def test_fmt_passes(self, go_single_ready: Path) -> None:
        result = mise("fmt", go_single_ready, timeout=60)
        assert result.returncode == 0, result.stderr

    def test_lint_passes(self, go_single_ready: Path) -> None:
        result = mise("lint", go_single_ready, timeout=120)
        assert result.returncode == 0, result.stderr

    def test_test_passes(self, go_single_ready: Path) -> None:
        result = mise("test", go_single_ready, timeout=60)
        assert result.returncode == 0, result.stderr
        assert (go_single_ready / "test-results" / "go-test.txt").exists(), (
            "go test must produce test-results/go-test.txt for CI artifact upload"
        )


class TestGoAppsHappyPath:
    def test_init_succeeds(self, go_apps_ready: Path) -> None:
        """Apps init must create per-module directories and workspace.toml."""
        assert (go_apps_ready / "apps" / "svc-a").is_dir()
        assert (go_apps_ready / "apps" / "svc-b").is_dir()
        assert (go_apps_ready / "workspace.toml").exists()

    def test_workspace_toml_lists_modules(self, go_apps_ready: Path) -> None:
        content = (go_apps_ready / "workspace.toml").read_text()
        assert "[modules.svc-a]" in content
        assert "[modules.svc-b]" in content

    def test_check_passes(self, go_apps_ready: Path) -> None:
        result = mise("check", go_apps_ready, timeout=300)
        assert result.returncode == 0, (
            f"check failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )


# ── Negative path: quality gates catch real errors ────────────────────────────


class TestGoGatesCatchErrors:
    def test_test_fails_on_compile_error(self, go_single_mut: Path) -> None:
        """A Go compile error must cause the test gate to fail."""
        bad_go = go_single_mut / "internal" / "app" / "broken.go"
        bad_go.write_text(
            "package app\n\n"
            "func BrokenFunc() string {\n"
            "    return 42  // type mismatch: int vs string\n"
            "}\n"
        )

        result = mise("test", go_single_mut, timeout=60)
        assert result.returncode != 0, "test should fail on compile error"

    def test_lint_fails_on_unchecked_error(self, go_single_mut: Path) -> None:
        """golangci-lint errcheck must flag an unchecked function return error."""
        bad_go = go_single_mut / "internal" / "app" / "unchecked.go"
        bad_go.write_text(
            "package app\n\n"
            'import "os"\n\n'
            "func deleteFile() {\n"
            '    os.Remove("somefile.txt")  // return error not checked\n'
            "}\n"
        )

        result = mise("lint", go_single_mut, timeout=120)
        assert result.returncode != 0, "lint should fail on unchecked os.Remove error"

    def test_fmt_check_fails_on_unformatted_code(self, go_single_mut: Path) -> None:
        """gofumpt must detect improperly formatted Go code."""
        bad_go = go_single_mut / "internal" / "app" / "unformatted.go"
        bad_go.write_text(
            'package app\nfunc unformatted()  string  {\nreturn "hello"\n}\n'
        )

        result = mise("fmt", go_single_mut, "--check", timeout=60)
        assert result.returncode != 0, "fmt --check should fail on unformatted Go code"

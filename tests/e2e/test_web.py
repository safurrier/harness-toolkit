"""E2E tests for the Web stack."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests._docs_helpers import (
    GENERATED_ADR,
    GENERATED_ARCHITECTURE,
    GENERATED_DECISION_LEDGER,
)
from tests._support import mise

pytestmark = [pytest.mark.e2e, pytest.mark.slow]


class TestWebSingleHappyPath:
    def test_init_layout(self, web_single_ready: Path) -> None:
        assert (web_single_ready / "package.json").exists()
        assert (web_single_ready / "wrangler.jsonc").exists()
        assert (web_single_ready / "src" / "app" / "App.tsx").exists()
        assert (web_single_ready / "worker" / "index.ts").exists()
        assert (
            web_single_ready / "migrations" / "0001_auth_and_saved_runs.sql"
        ).exists()

    def test_scaffold_artifacts_removed(self, web_single_ready: Path) -> None:
        assert not (web_single_ready / "stacks").exists()
        assert not (web_single_ready / "templates").exists()
        assert not (web_single_ready / "src" / "harness_toolkit").exists()
        assert not (web_single_ready / "tests" / "e2e").exists()
        assert not (web_single_ready / "tests" / "unit").exists()
        assert not (web_single_ready / "tests" / "contract").exists()

    def test_spec_md_generated(self, web_single_ready: Path) -> None:
        spec = web_single_ready / "SPEC.md"
        assert spec.exists()
        content = spec.read_text()
        assert content.startswith("---\n")
        assert "Invariants" in content

    def test_agents_md_exists(self, web_single_ready: Path) -> None:
        content = (web_single_ready / "AGENTS.md").read_text()
        assert "testwebapp" in content
        assert "## Working agreement" in content
        assert "## Skills" in content
        assert "mise run verify" in content

    def test_claude_md_points_to_agents_md(self, web_single_ready: Path) -> None:
        claude = web_single_ready / "CLAUDE.md"
        agents = web_single_ready / "AGENTS.md"
        assert claude.exists()
        if claude.is_symlink():
            assert claude.resolve() == agents.resolve()
        else:
            assert claude.read_text() == agents.read_text()

    def test_docs_architecture_exists(self, web_single_ready: Path) -> None:
        arch = web_single_ready / GENERATED_ARCHITECTURE
        assert arch.exists()
        content = arch.read_text()
        assert "## 3. Invariants & Boundaries" in content
        assert "Worktree Safety" in content

    def test_decision_ledger_exists(self, web_single_ready: Path) -> None:
        ledger = web_single_ready / GENERATED_DECISION_LEDGER
        assert ledger.exists()
        assert "Append-only" in ledger.read_text()

    def test_docs_decisions_exists(self, web_single_ready: Path) -> None:
        adr = web_single_ready / GENERATED_ADR
        assert adr.exists()
        assert "web" in adr.read_text().lower()

    def test_agent_skills_exists(self, web_single_ready: Path) -> None:
        skills = web_single_ready / ".agent" / "skills"
        assert (skills / "README.md").exists()
        assert (skills / "example-skill" / "SKILL.md").exists()
        assert (skills / "create-project-verification" / "SKILL.md").exists()
        assert (skills / "maintain-project-verification" / "SKILL.md").exists()

    def test_ci_workflow_is_two_tier(self, web_single_ready: Path) -> None:
        ci = web_single_ready / ".github" / "workflows" / "ci.yml"
        content = ci.read_text()
        assert "mise run ci" in content
        assert "mise run verify" in content
        assert "sync-check" not in content
        assert "mise run verify" in content
        assert "upload-artifact" in content

    def test_mise_toml_has_web_tools(self, web_single_ready: Path) -> None:
        content = (web_single_ready / ".mise.toml").read_text()
        assert 'SCAFFOLD_PROJECT_STACK = "web"' in content
        assert 'SCAFFOLD_PROJECT_SHAPE = "single"' in content
        assert 'node = "22"' in content

    def test_package_json_has_expected_scripts(self, web_single_ready: Path) -> None:
        content = (web_single_ready / "package.json").read_text()
        assert '"check":' in content
        assert '"deploy:dry-run":' in content
        assert '"db:migrate:local":' in content

    def test_check_passes(self, web_single_ready: Path) -> None:
        result = mise("check", web_single_ready, timeout=240)
        assert result.returncode == 0, (
            f"check failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )

    def test_fmt_passes(self, web_single_ready: Path) -> None:
        result = mise("fmt", web_single_ready, timeout=120)
        assert result.returncode == 0, result.stderr

    def test_lint_passes(self, web_single_ready: Path) -> None:
        result = mise("lint", web_single_ready, timeout=120)
        assert result.returncode == 0, result.stderr

    def test_typecheck_passes(self, web_single_ready: Path) -> None:
        result = mise("typecheck", web_single_ready, timeout=120)
        assert result.returncode == 0, result.stderr

    def test_test_passes(self, web_single_ready: Path) -> None:
        result = mise("test", web_single_ready, timeout=120)
        assert result.returncode == 0, result.stderr
        assert (web_single_ready / "test-results" / "vitest.txt").exists()

    def test_build_passes(self, web_single_ready: Path) -> None:
        result = mise("build", web_single_ready, timeout=180)
        assert result.returncode == 0, result.stderr
        assert (web_single_ready / "dist" / "index.html").exists()


class TestWebAppsHappyPath:
    def test_init_succeeds(self, web_apps_ready: Path) -> None:
        assert (web_apps_ready / "apps" / "ui").is_dir()
        assert (web_apps_ready / "apps" / "admin").is_dir()
        assert (web_apps_ready / "workspace.toml").exists()

    def test_workspace_toml_lists_modules(self, web_apps_ready: Path) -> None:
        content = (web_apps_ready / "workspace.toml").read_text()
        assert "[modules.ui]" in content
        assert "[modules.admin]" in content
        assert 'kind = "web"' in content

    def test_each_module_has_web_app(self, web_apps_ready: Path) -> None:
        for module in ["ui", "admin"]:
            root = web_apps_ready / "apps" / module
            assert (root / "package.json").exists()
            assert (root / "wrangler.jsonc").exists()
            assert (root / "worker" / "index.ts").exists()

    def test_check_passes(self, web_apps_ready: Path) -> None:
        result = mise("check", web_apps_ready, timeout=360)
        assert result.returncode == 0, (
            f"check failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )


class TestWebGatesCatchErrors:
    def test_fmt_check_fails_on_unformatted_code(self, web_single_mut: Path) -> None:
        bad_file = web_single_mut / "src" / "app" / "bad-format.ts"
        bad_file.write_text("export const value={a:1,b:2}\n")

        result = mise("fmt", web_single_mut, "--check", timeout=120)
        assert result.returncode != 0

    def test_lint_fails_on_unused_variable(self, web_single_mut: Path) -> None:
        bad_file = web_single_mut / "src" / "app" / "bad-lint.ts"
        bad_file.write_text("const unused = 1;\nexport const value = 2;\n")

        result = mise("lint", web_single_mut, timeout=120)
        assert result.returncode != 0

    def test_typecheck_fails_on_wrong_type(self, web_single_mut: Path) -> None:
        bad_file = web_single_mut / "src" / "app" / "bad-type.ts"
        bad_file.write_text("export const count: number = 'not a number';\n")

        result = mise("typecheck", web_single_mut, timeout=120)
        assert result.returncode != 0

    def test_test_fails_on_failing_assertion(self, web_single_mut: Path) -> None:
        (web_single_mut / "tests").mkdir(exist_ok=True)
        bad_test = web_single_mut / "tests" / "failing.test.ts"
        bad_test.write_text(
            "import { expect, it } from 'vitest';\n"
            "it('fails', () => { expect(true).toBe(false); });\n"
        )

        result = mise("test", web_single_mut, timeout=120)
        assert result.returncode != 0

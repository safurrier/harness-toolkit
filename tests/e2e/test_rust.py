"""E2E tests for the Rust stack.

Marked ``slow`` because Rust compilation can take minutes on a cold cache.
Deselect them during day-to-day development:

    pytest -m "not slow"
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from tests._docs_helpers import (
    GENERATED_ADR,
    GENERATED_ARCHITECTURE,
    GENERATED_DECISION_LEDGER,
)
from tests._support import mise

pytestmark = [pytest.mark.e2e, pytest.mark.slow, pytest.mark.rust]


# ── Happy path ────────────────────────────────────────────────────────────────


class TestRustSingleHappyPath:
    def test_init_layout(self, rust_single_ready: Path) -> None:
        """Init must produce the expected Rust project layout."""
        assert (rust_single_ready / "Cargo.toml").exists()
        assert (rust_single_ready / "src" / "main.rs").exists()
        assert (rust_single_ready / "src" / "lib.rs").exists()
        assert (rust_single_ready / "Dockerfile").exists()

    def test_scaffold_artifacts_removed(self, rust_single_ready: Path) -> None:
        assert not (rust_single_ready / "stacks").exists()
        assert not (rust_single_ready / "templates").exists()
        assert not (rust_single_ready / "src" / "harness_toolkit").exists()

    def test_spec_md_generated(self, rust_single_ready: Path) -> None:
        """SPEC.md must be generated from template."""
        spec = rust_single_ready / "SPEC.md"
        assert spec.exists()
        assert spec.read_text().startswith("---\n"), "SPEC.md missing frontmatter"

    def test_agents_md_exists(self, rust_single_ready: Path) -> None:
        """AGENTS.md must be generated as the canonical steering doc."""
        assert (rust_single_ready / "AGENTS.md").exists()
        content = (rust_single_ready / "AGENTS.md").read_text()
        assert "## Working agreement" in content
        assert "## Skills" in content
        assert "mise run verify" in content

    def test_claude_md_points_to_agents_md(self, rust_single_ready: Path) -> None:
        """CLAUDE.md must be a symlink or copy of AGENTS.md."""
        claude = rust_single_ready / "CLAUDE.md"
        agents = rust_single_ready / "AGENTS.md"
        assert claude.exists()
        if claude.is_symlink():
            assert claude.resolve() == agents.resolve()
        else:
            assert claude.read_text() == agents.read_text()

    def test_docs_architecture_exists(self, rust_single_ready: Path) -> None:
        """The explanation architecture doc must be generated with invariant sections."""
        arch = rust_single_ready / GENERATED_ARCHITECTURE
        assert arch.exists()
        content = arch.read_text()
        assert "Invariants" in content
        assert "Worktree Safety" in content

    def test_decision_ledger_exists(self, rust_single_ready: Path) -> None:
        ledger = rust_single_ready / GENERATED_DECISION_LEDGER
        assert ledger.exists()
        assert "append-only" in ledger.read_text().lower()

    def test_docs_decisions_exists(self, rust_single_ready: Path) -> None:
        """The explanation decisions dir must contain the initial stack-choice ADR."""
        adr = rust_single_ready / GENERATED_ADR
        assert adr.exists()
        assert "rust" in adr.read_text().lower()

    def test_agent_skills_exists(self, rust_single_ready: Path) -> None:
        """.agent/skills/ must have workflow skills and the starter template."""
        skills = rust_single_ready / ".agent" / "skills"
        assert skills.is_dir()
        assert (skills / "README.md").exists()
        assert (skills / "example-skill" / "SKILL.md").exists()
        assert (skills / "create-project-verification" / "SKILL.md").exists()
        assert (skills / "maintain-project-verification" / "SKILL.md").exists()
        assert not (skills / "slice-workflow").exists()

    def test_claude_skills_symlink(self, rust_single_ready: Path) -> None:
        """.claude/skills must point to .agent/skills."""
        claude_skills = rust_single_ready / ".claude" / "skills"
        agent_skills = rust_single_ready / ".agent" / "skills"
        assert claude_skills.exists()
        if claude_skills.is_symlink():
            assert claude_skills.resolve() == agent_skills.resolve()
        else:
            assert claude_skills.is_dir()

    def test_ci_workflow_is_two_tier(self, rust_single_ready: Path) -> None:
        """Generated CI must have check + sync + verify jobs with artifact upload."""
        ci = rust_single_ready / ".github" / "workflows" / "ci.yml"
        assert ci.exists()
        content = ci.read_text()
        assert "mise run ci" in content
        assert "mise run verify" in content
        assert "--changed-from" in content
        assert "sync-check" not in content
        assert "mise run verify" in content
        assert "upload-artifact" in content

    def test_mise_toml_has_rust_tools(self, rust_single_ready: Path) -> None:
        content = (rust_single_ready / ".mise.toml").read_text()
        assert "rust = " in content

    def test_cargo_toml_has_correct_name(self, rust_single_ready: Path) -> None:
        content = (rust_single_ready / "Cargo.toml").read_text()
        assert 'name = "testrustapp"' in content

    def test_check_passes(self, rust_single_ready: Path) -> None:
        """``mise run check`` must exit 0 on a freshly initialized Rust project."""
        result = mise("check", rust_single_ready, timeout=300)
        assert result.returncode == 0, (
            f"check failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )

    def test_fmt_passes(self, rust_single_ready: Path) -> None:
        result = mise("fmt", rust_single_ready, timeout=60)
        assert result.returncode == 0, result.stderr

    def test_lint_passes(self, rust_single_ready: Path) -> None:
        result = mise("lint", rust_single_ready, timeout=120)
        assert result.returncode == 0, result.stderr

    def test_test_passes(self, rust_single_ready: Path) -> None:
        result = mise("test", rust_single_ready, timeout=120)
        assert result.returncode == 0, result.stderr
        assert (rust_single_ready / "test-results" / "cargo-test.txt").exists(), (
            "cargo test must produce test-results/cargo-test.txt for CI artifact upload"
        )

    def test_release_build(self, rust_single_ready: Path) -> None:
        """``cargo build --release`` must produce a working binary."""
        result = mise("build", rust_single_ready, timeout=120)
        assert result.returncode == 0, (
            f"release build failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
        binary = rust_single_ready / "target" / "release" / "testrustapp"
        assert binary.exists(), "release binary not found"

        run = subprocess.run(
            [str(binary)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert run.returncode == 0, f"binary exited {run.returncode}: {run.stderr}"
        assert "testrustapp" in run.stdout.lower() or "hello" in run.stdout.lower(), (
            f"binary output unexpected: {run.stdout!r}"
        )


class TestRustAppsHappyPath:
    def test_init_succeeds(self, rust_apps_ready: Path) -> None:
        """Apps init must create per-module directories and workspace.toml."""
        assert (rust_apps_ready / "apps" / "svc-a").is_dir()
        assert (rust_apps_ready / "apps" / "svc-b").is_dir()
        assert (rust_apps_ready / "workspace.toml").exists()

    def test_workspace_toml_lists_modules(self, rust_apps_ready: Path) -> None:
        content = (rust_apps_ready / "workspace.toml").read_text()
        assert "[modules.svc-a]" in content
        assert "[modules.svc-b]" in content

    def test_check_passes(self, rust_apps_ready: Path) -> None:
        result = mise("check", rust_apps_ready, timeout=300)
        assert result.returncode == 0, (
            f"check failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )

    def test_test_fails_on_compile_error(self, rust_single_mut: Path) -> None:
        """A Rust compile error must cause the test gate to fail."""
        bad_rs = rust_single_mut / "src" / "broken.rs"
        bad_rs.write_text(
            "pub fn broken() -> String {\n"
            "    42  // mismatched types: expected String, found i32\n"
            "}\n"
        )
        # Include the broken module in lib.rs
        lib_rs = rust_single_mut / "src" / "lib.rs"
        content = lib_rs.read_text()
        lib_rs.write_text(f"pub mod broken;\n{content}")

        result = mise("test", rust_single_mut, timeout=120)
        assert result.returncode != 0, "test should fail on compile error"

    def test_lint_fails_on_clippy_warning(self, rust_single_mut: Path) -> None:
        """cargo clippy must flag common mistakes."""
        bad_rs = rust_single_mut / "src" / "clippy_bad.rs"
        bad_rs.write_text(
            "#[allow(dead_code)]\n"
            "fn clippy_bad() {\n"
            "    let x: f64 = 3.14;\n"
            "    if x == f64::NAN {\n"
            '        println!("nan");\n'
            "    }\n"
            "}\n"
        )
        lib_rs = rust_single_mut / "src" / "lib.rs"
        content = lib_rs.read_text()
        lib_rs.write_text(f"pub mod clippy_bad;\n{content}")

        result = mise("lint", rust_single_mut, timeout=120)
        assert result.returncode != 0, "lint should fail on clippy warning"

    def test_fmt_check_fails_on_unformatted_code(self, rust_single_mut: Path) -> None:
        """cargo fmt must detect improperly formatted Rust code."""
        bad_rs = rust_single_mut / "src" / "unformatted.rs"
        bad_rs.write_text('pub fn unformatted(   ) ->String{  "hello".to_string()}\n')
        lib_rs = rust_single_mut / "src" / "lib.rs"
        content = lib_rs.read_text()
        lib_rs.write_text(f"pub mod unformatted;\n{content}")

        result = mise("fmt", rust_single_mut, "--check", timeout=60)
        assert result.returncode != 0, (
            "fmt --check should fail on unformatted Rust code"
        )

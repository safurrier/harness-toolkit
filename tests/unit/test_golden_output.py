"""Golden output tests — verify generated file content is deterministic.

These tests call run_init() directly as a Python function (no subprocess
through mise, no network). They are fast and belong in the unit test layer.

Note: run_init() calls git_init() internally (subprocess git in tmp_path),
which is acceptable for these tests.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from harness_toolkit.scaffold.config import Config
from harness_toolkit.scaffold.init import run_init
from tests._docs_helpers import (
    ARCHITECTURE_REQUIRED_SECTIONS,
    GENERATED_ADR,
    GENERATED_ARCHITECTURE,
    SPEC_REQUIRED_SECTIONS,
    find_adrs,
    find_section,
    has_frontmatter,
    parse_sections,
    validate_adr,
)
from tests._support import COPY_IGNORE, SCAFFOLD_ROOT

pytestmark = pytest.mark.integration

# Fixed test constants — same across all golden tests
_NAME = "goldenapp"


# ── helpers ────────────────────────────────────────────────────────────────


def _scaffold_copy(tmp_path: Path) -> Path:
    """Copy the scaffold into tmp_path for direct run_init() use."""
    dest = tmp_path / "scaffold"
    shutil.copytree(SCAFFOLD_ROOT, dest, ignore=COPY_IGNORE)
    return dest


def _init(
    root: Path,
    *,
    shape: str,
    stack: str,
    modules: list[str] | None = None,
) -> Path:
    """Run run_init directly and return root."""
    config = Config(
        name=_NAME,
        description="A golden test project",
        shape=shape,
        stack=stack,
        modules=modules or [],
        author_name="Test Author",
        author_email="test@example.com",
        go_module="github.com/test-org/goldenapp" if stack == "go" else "",
        install_hooks=False,
        keep_examples=True,
    )
    run_init(root, config)
    return root


def test_apps_modules_cannot_escape_project_root(tmp_path: Path) -> None:
    root = _scaffold_copy(tmp_path)
    config = Config(
        name=_NAME,
        description="A golden test project",
        shape="apps",
        stack="python",
        modules=["../../outside"],
        author_name="Test Author",
        author_email="test@example.com",
        install_hooks=False,
        keep_examples=True,
    )

    with pytest.raises(ValueError):
        run_init(root, config)

    assert not (tmp_path / "outside").exists()


# ── Python Single ────────────────────────────────────────────────────────


class TestPythonSingleGolden:
    @pytest.fixture(autouse=True)
    def project(self, tmp_path: Path) -> None:
        self._root = _init(_scaffold_copy(tmp_path), shape="single", stack="python")

    def test_mise_toml_content(self) -> None:
        content = (self._root / ".mise.toml").read_text()
        assert 'SCAFFOLD_PROJECT_NAME  = "goldenapp"' in content
        assert 'SCAFFOLD_PROJECT_STACK = "python"' in content
        assert 'SCAFFOLD_PROJECT_SHAPE = "single"' in content
        assert 'python = "3.12"' in content
        assert 'uv = "latest"' in content

    def test_pyproject_toml_has_project_name(self) -> None:
        content = (self._root / "pyproject.toml").read_text()
        assert 'name = "goldenapp"' in content
        assert "pytest" in content

    def test_readme_has_project_name(self) -> None:
        content = (self._root / "README.md").read_text()
        assert "goldenapp" in content

    def test_readme_documents_quality_and_verification_workflow(self) -> None:
        content = (self._root / "README.md").read_text()
        assert "mise run check" in content
        assert "mise run verify" in content
        assert "mise run plan" not in content

    def test_agents_md_documents_verification_contract(self) -> None:
        content = (self._root / "AGENTS.md").read_text()
        assert "goldenapp" in content
        assert "## Working agreement" in content
        assert "## Skills" in content
        assert "mise run verify" in content
        assert "mise run plan" not in content

    def test_agents_md_no_frontmatter(self) -> None:
        content = (self._root / "AGENTS.md").read_text()
        assert not content.startswith("---\n"), "AGENTS.md should not have frontmatter"

    def test_architecture_doc_has_frontmatter(self) -> None:
        content = (self._root / GENERATED_ARCHITECTURE).read_text()
        assert content.startswith("---\n"), "architecture.md missing frontmatter"
        assert "id:" in content

    def test_adr_has_frontmatter(self) -> None:
        content = (self._root / GENERATED_ADR).read_text()
        assert content.startswith("---\n"), "ADR missing frontmatter"
        assert "id:" in content

    def test_docs_test_generated(self) -> None:
        assert (self._root / "tests" / "test_docs.py").exists()

    def test_gitignore_has_python_entries(self) -> None:
        content = (self._root / ".gitignore").read_text()
        assert "__pycache__/" in content
        assert ".venv/" in content

    def test_ci_workflow_content(self) -> None:
        content = (self._root / ".github" / "workflows" / "ci.yml").read_text()
        assert "mise run ci" in content
        assert "mise run verify" in content
        assert "upload-artifact" in content

    def test_architecture_doc(self) -> None:
        content = (self._root / GENERATED_ARCHITECTURE).read_text()
        assert "Invariants" in content

    def test_architecture_has_required_sections(self) -> None:
        arch = self._root / GENERATED_ARCHITECTURE
        sections = parse_sections(arch)
        for name in ARCHITECTURE_REQUIRED_SECTIONS:
            assert find_section(sections, name, level=2) is not None, (
                f"Generated architecture.md missing section '{name}'"
            )

    def test_architecture_decisions_index(self) -> None:
        sections = parse_sections(self._root / GENERATED_ARCHITECTURE)
        dec = find_section(sections, "Decisions", level=2)
        assert dec is not None
        assert "0001-stack-choice" in dec.content, (
            "Decisions index doesn't reference initial ADR"
        )

    def test_adr_mentions_stack(self) -> None:
        content = (self._root / GENERATED_ADR).read_text()
        assert "python" in content

    def test_adr_schema_valid(self) -> None:
        adrs = find_adrs((self._root / GENERATED_ADR).parent)
        assert len(adrs) >= 1, "Expected at least one ADR"
        for adr in adrs:
            errors = validate_adr(adr)
            assert not errors, f"ADR {adr.filename} errors: {'; '.join(errors)}"

    def test_adr_has_generated_from(self) -> None:
        adrs = find_adrs((self._root / GENERATED_ADR).parent)
        assert adrs[0].generated_from == "init"

    def test_spec_md_exists(self) -> None:
        assert (self._root / "SPEC.md").exists()

    def test_spec_md_has_frontmatter(self) -> None:
        assert has_frontmatter(self._root / "SPEC.md")

    def test_spec_md_has_required_sections(self) -> None:
        sections = parse_sections(self._root / "SPEC.md")
        for name in SPEC_REQUIRED_SECTIONS:
            assert find_section(sections, name, level=2) is not None, (
                f"Generated SPEC.md missing section '{name}'"
            )

    def test_spec_md_has_project_name(self) -> None:
        content = (self._root / "SPEC.md").read_text()
        assert "goldenapp" in content

    def test_retired_plan_templates_are_not_generated(self) -> None:
        assert not (self._root / ".ai" / "plans").exists()

    def test_scaffold_artifacts_removed(self) -> None:
        assert not (self._root / "stacks").exists()
        assert not (self._root / "templates").exists()

    def test_readme_dev_command_no_module(self) -> None:
        content = (self._root / "README.md").read_text()
        assert "mise run dev" in content
        assert "mise run dev -- api" not in content

    def test_agent_skills_generated(self) -> None:
        assert (self._root / ".agent" / "skills" / "README.md").exists()
        assert (
            self._root / ".agent" / "skills" / "example-skill" / "SKILL.md"
        ).exists()


# ── Python Apps ──────────────────────────────────────────────────────────


class TestPythonAppsGolden:
    @pytest.fixture(autouse=True)
    def project(self, tmp_path: Path) -> None:
        self._root = _init(
            _scaffold_copy(tmp_path),
            shape="apps",
            stack="python",
            modules=["api", "worker"],
        )

    def test_workspace_toml_structure(self) -> None:
        content = (self._root / "workspace.toml").read_text()
        assert "[modules.api]" in content
        assert "[modules.worker]" in content
        assert "apps/api" in content
        assert "apps/worker" in content

    def test_gitignore_exists(self) -> None:
        gi = self._root / ".gitignore"
        assert gi.exists()
        content = gi.read_text()
        assert "__pycache__/" in content

    def test_mise_toml_apps_shape(self) -> None:
        content = (self._root / ".mise.toml").read_text()
        assert 'SCAFFOLD_PROJECT_SHAPE = "apps"' in content

    def test_per_module_pyproject(self) -> None:
        for mod in ["api", "worker"]:
            pyproj = self._root / "apps" / mod / "pyproject.toml"
            assert pyproj.exists(), f"Missing pyproject.toml for {mod}"

    def test_agents_md_no_frontmatter(self) -> None:
        content = (self._root / "AGENTS.md").read_text()
        assert not content.startswith("---\n"), "AGENTS.md should not have frontmatter"

    def test_architecture_doc_has_frontmatter(self) -> None:
        content = (self._root / GENERATED_ARCHITECTURE).read_text()
        assert content.startswith("---\n"), "architecture.md missing frontmatter"
        assert "id:" in content

    def test_adr_has_frontmatter(self) -> None:
        content = (self._root / GENERATED_ADR).read_text()
        assert content.startswith("---\n"), "ADR missing frontmatter"
        assert "id:" in content

    def test_architecture_has_required_sections(self) -> None:
        sections = parse_sections(self._root / GENERATED_ARCHITECTURE)
        for name in ARCHITECTURE_REQUIRED_SECTIONS:
            assert find_section(sections, name, level=2) is not None, (
                f"Generated architecture.md missing section '{name}'"
            )

    def test_adr_schema_valid(self) -> None:
        adrs = find_adrs((self._root / GENERATED_ADR).parent)
        assert len(adrs) >= 1
        for adr in adrs:
            errors = validate_adr(adr)
            assert not errors, f"ADR {adr.filename} errors: {'; '.join(errors)}"

    def test_spec_md_exists(self) -> None:
        assert (self._root / "SPEC.md").exists()

    def test_spec_md_has_required_sections(self) -> None:
        sections = parse_sections(self._root / "SPEC.md")
        for name in SPEC_REQUIRED_SECTIONS:
            assert find_section(sections, name, level=2) is not None, (
                f"Generated SPEC.md missing section '{name}'"
            )

    def test_retired_plan_templates_are_not_generated(self) -> None:
        assert not (self._root / ".ai" / "plans").exists()

    def test_readme_dev_command_shows_module(self) -> None:
        content = (self._root / "README.md").read_text()
        assert "mise run dev -- <module>" in content

    def test_agents_md_documents_verification_contract(self) -> None:
        content = (self._root / "AGENTS.md").read_text()
        assert "scripts/verify-routes --path" in content
        assert "mise run plan" not in content

    def test_ci_workflow_apps_artifacts(self) -> None:
        content = (self._root / ".github" / "workflows" / "ci.yml").read_text()
        assert "apps/*/test-results/" in content

    def test_scaffold_artifacts_removed(self) -> None:
        assert not (self._root / "stacks").exists()
        assert not (self._root / "templates").exists()


# ── Go Single ────────────────────────────────────────────────────────────


class TestGoSingleGolden:
    @pytest.fixture(autouse=True)
    def project(self, tmp_path: Path) -> None:
        self._root = _init(_scaffold_copy(tmp_path), shape="single", stack="go")

    def test_go_mod_content(self) -> None:
        content = (self._root / "go.mod").read_text()
        assert "github.com/test-org/goldenapp" in content

    def test_mise_toml_go_tools(self) -> None:
        content = (self._root / ".mise.toml").read_text()
        assert 'python = "3.12"' in content
        assert 'uv = "latest"' in content
        assert "go = " in content
        assert "gofumpt" in content
        assert "golangci-lint" in content

    def test_gitignore_has_go_entries(self) -> None:
        content = (self._root / ".gitignore").read_text()
        assert "bin/" in content

    def test_dockerfile_generated(self) -> None:
        assert (self._root / "Dockerfile").exists()

    def test_golangci_yml_generated(self) -> None:
        assert (self._root / ".golangci.yml").exists()

    def test_agents_md_no_frontmatter(self) -> None:
        content = (self._root / "AGENTS.md").read_text()
        assert not content.startswith("---\n"), "AGENTS.md should not have frontmatter"

    def test_architecture_doc_has_frontmatter(self) -> None:
        content = (self._root / GENERATED_ARCHITECTURE).read_text()
        assert content.startswith("---\n"), "architecture.md missing frontmatter"
        assert "id:" in content

    def test_adr_has_frontmatter(self) -> None:
        content = (self._root / GENERATED_ADR).read_text()
        assert content.startswith("---\n"), "ADR missing frontmatter"
        assert "id:" in content

    def test_architecture_has_required_sections(self) -> None:
        sections = parse_sections(self._root / GENERATED_ARCHITECTURE)
        for name in ARCHITECTURE_REQUIRED_SECTIONS:
            assert find_section(sections, name, level=2) is not None, (
                f"Generated architecture.md missing section '{name}'"
            )

    def test_adr_schema_valid(self) -> None:
        adrs = find_adrs((self._root / GENERATED_ADR).parent)
        assert len(adrs) >= 1
        for adr in adrs:
            errors = validate_adr(adr)
            assert not errors, f"ADR {adr.filename} errors: {'; '.join(errors)}"

    def test_spec_md_exists(self) -> None:
        assert (self._root / "SPEC.md").exists()

    def test_spec_md_has_required_sections(self) -> None:
        sections = parse_sections(self._root / "SPEC.md")
        for name in SPEC_REQUIRED_SECTIONS:
            assert find_section(sections, name, level=2) is not None, (
                f"Generated SPEC.md missing section '{name}'"
            )

    def test_readme_has_project_name(self) -> None:
        content = (self._root / "README.md").read_text()
        assert "goldenapp" in content

    def test_readme_documents_quality_and_verification_workflow(self) -> None:
        content = (self._root / "README.md").read_text()
        assert "mise run check" in content
        assert "mise run verify" in content
        assert "mise run plan" not in content

    def test_agents_md_documents_verification_contract(self) -> None:
        content = (self._root / "AGENTS.md").read_text()
        assert "goldenapp" in content
        assert "## Working agreement" in content
        assert "## Skills" in content
        assert "mise run verify" in content
        assert "mise run plan" not in content

    def test_spec_md_has_frontmatter(self) -> None:
        assert has_frontmatter(self._root / "SPEC.md")

    def test_spec_md_has_project_name(self) -> None:
        content = (self._root / "SPEC.md").read_text()
        assert "goldenapp" in content

    def test_architecture_decisions_index(self) -> None:
        sections = parse_sections(self._root / GENERATED_ARCHITECTURE)
        dec = find_section(sections, "Decisions", level=2)
        assert dec is not None
        assert "0001-stack-choice" in dec.content, (
            "Decisions index doesn't reference initial ADR"
        )

    def test_adr_mentions_stack(self) -> None:
        content = (self._root / GENERATED_ADR).read_text()
        assert "go" in content.lower()

    def test_adr_has_generated_from(self) -> None:
        adrs = find_adrs((self._root / GENERATED_ADR).parent)
        assert adrs[0].generated_from == "init"

    def test_ci_workflow_content(self) -> None:
        content = (self._root / ".github" / "workflows" / "ci.yml").read_text()
        assert "mise run ci" in content
        assert "mise run verify" in content
        assert "upload-artifact" in content

    def test_retired_plan_templates_are_not_generated(self) -> None:
        assert not (self._root / ".ai" / "plans").exists()

    def test_readme_dev_command_no_module(self) -> None:
        content = (self._root / "README.md").read_text()
        assert "mise run dev" in content
        assert "mise run dev -- api" not in content

    def test_agent_skills_generated(self) -> None:
        assert (self._root / ".agent" / "skills" / "README.md").exists()
        assert (
            self._root / ".agent" / "skills" / "example-skill" / "SKILL.md"
        ).exists()

    def test_scaffold_artifacts_removed(self) -> None:
        assert not (self._root / "stacks").exists()
        assert not (self._root / "templates").exists()


# ── Go Apps ──────────────────────────────────────────────────────────────


class TestGoAppsGolden:
    @pytest.fixture(autouse=True)
    def project(self, tmp_path: Path) -> None:
        self._root = _init(
            _scaffold_copy(tmp_path),
            shape="apps",
            stack="go",
            modules=["svc-a", "svc-b"],
        )

    def test_workspace_toml(self) -> None:
        content = (self._root / "workspace.toml").read_text()
        assert "[modules.svc-a]" in content
        assert "[modules.svc-b]" in content

    def test_per_module_go_mod(self) -> None:
        for mod in ["svc-a", "svc-b"]:
            go_mod = self._root / "apps" / mod / "go.mod"
            assert go_mod.exists(), f"Missing go.mod for {mod}"

    def test_gitignore_exists(self) -> None:
        assert (self._root / ".gitignore").exists()

    def test_agents_md_no_frontmatter(self) -> None:
        content = (self._root / "AGENTS.md").read_text()
        assert not content.startswith("---\n"), "AGENTS.md should not have frontmatter"

    def test_architecture_doc_has_frontmatter(self) -> None:
        content = (self._root / GENERATED_ARCHITECTURE).read_text()
        assert content.startswith("---\n"), "architecture.md missing frontmatter"
        assert "id:" in content

    def test_adr_has_frontmatter(self) -> None:
        content = (self._root / GENERATED_ADR).read_text()
        assert content.startswith("---\n"), "ADR missing frontmatter"
        assert "id:" in content

    def test_architecture_has_required_sections(self) -> None:
        sections = parse_sections(self._root / GENERATED_ARCHITECTURE)
        for name in ARCHITECTURE_REQUIRED_SECTIONS:
            assert find_section(sections, name, level=2) is not None, (
                f"Generated architecture.md missing section '{name}'"
            )

    def test_adr_schema_valid(self) -> None:
        adrs = find_adrs((self._root / GENERATED_ADR).parent)
        assert len(adrs) >= 1
        for adr in adrs:
            errors = validate_adr(adr)
            assert not errors, f"ADR {adr.filename} errors: {'; '.join(errors)}"

    def test_spec_md_exists(self) -> None:
        assert (self._root / "SPEC.md").exists()

    def test_spec_md_has_required_sections(self) -> None:
        sections = parse_sections(self._root / "SPEC.md")
        for name in SPEC_REQUIRED_SECTIONS:
            assert find_section(sections, name, level=2) is not None, (
                f"Generated SPEC.md missing section '{name}'"
            )

    def test_retired_plan_templates_are_not_generated(self) -> None:
        assert not (self._root / ".ai" / "plans").exists()

    def test_readme_dev_command_shows_module(self) -> None:
        content = (self._root / "README.md").read_text()
        assert "mise run dev -- <module>" in content

    def test_agents_md_documents_verification_contract(self) -> None:
        content = (self._root / "AGENTS.md").read_text()
        assert "scripts/verify-routes --path" in content
        assert "mise run plan" not in content

    def test_ci_workflow_apps_artifacts(self) -> None:
        content = (self._root / ".github" / "workflows" / "ci.yml").read_text()
        assert "apps/*/test-results/" in content

    def test_scaffold_artifacts_removed(self) -> None:
        assert not (self._root / "stacks").exists()
        assert not (self._root / "templates").exists()


# ── Rust Single ───────────────────────────────────────────────────────────


class TestRustSingleGolden:
    @pytest.fixture(autouse=True)
    def project(self, tmp_path: Path) -> None:
        self._root = _init(_scaffold_copy(tmp_path), shape="single", stack="rust")

    def test_cargo_toml_content(self) -> None:
        content = (self._root / "Cargo.toml").read_text()
        assert 'name = "goldenapp"' in content

    def test_mise_toml_rust_tools(self) -> None:
        content = (self._root / ".mise.toml").read_text()
        assert 'python = "3.12"' in content
        assert 'uv = "latest"' in content
        assert 'rust = "stable"' in content

    def test_gitignore_has_rust_entries(self) -> None:
        content = (self._root / ".gitignore").read_text()
        assert "/target/" in content

    def test_dockerfile_generated(self) -> None:
        assert (self._root / "Dockerfile").exists()

    def test_rustfmt_toml_generated(self) -> None:
        assert (self._root / "rustfmt.toml").exists()

    def test_agents_md_no_frontmatter(self) -> None:
        content = (self._root / "AGENTS.md").read_text()
        assert not content.startswith("---\n"), "AGENTS.md should not have frontmatter"

    def test_architecture_doc_has_frontmatter(self) -> None:
        content = (self._root / GENERATED_ARCHITECTURE).read_text()
        assert content.startswith("---\n"), "architecture.md missing frontmatter"
        assert "id:" in content

    def test_adr_has_frontmatter(self) -> None:
        content = (self._root / GENERATED_ADR).read_text()
        assert content.startswith("---\n"), "ADR missing frontmatter"
        assert "id:" in content

    def test_architecture_has_required_sections(self) -> None:
        sections = parse_sections(self._root / GENERATED_ARCHITECTURE)
        for name in ARCHITECTURE_REQUIRED_SECTIONS:
            assert find_section(sections, name, level=2) is not None, (
                f"Generated architecture.md missing section '{name}'"
            )

    def test_adr_schema_valid(self) -> None:
        adrs = find_adrs((self._root / GENERATED_ADR).parent)
        assert len(adrs) >= 1
        for adr in adrs:
            errors = validate_adr(adr)
            assert not errors, f"ADR {adr.filename} errors: {'; '.join(errors)}"

    def test_readme_has_project_name(self) -> None:
        content = (self._root / "README.md").read_text()
        assert "goldenapp" in content

    def test_readme_documents_quality_and_verification_workflow(self) -> None:
        content = (self._root / "README.md").read_text()
        assert "mise run check" in content
        assert "mise run verify" in content
        assert "mise run plan" not in content

    def test_agents_md_documents_verification_contract(self) -> None:
        content = (self._root / "AGENTS.md").read_text()
        assert "goldenapp" in content
        assert "## Working agreement" in content
        assert "## Skills" in content
        assert "mise run verify" in content
        assert "mise run plan" not in content

    def test_spec_md_has_frontmatter(self) -> None:
        assert has_frontmatter(self._root / "SPEC.md")

    def test_spec_md_has_project_name(self) -> None:
        content = (self._root / "SPEC.md").read_text()
        assert "goldenapp" in content

    def test_architecture_decisions_index(self) -> None:
        sections = parse_sections(self._root / GENERATED_ARCHITECTURE)
        dec = find_section(sections, "Decisions", level=2)
        assert dec is not None
        assert "0001-stack-choice" in dec.content, (
            "Decisions index doesn't reference initial ADR"
        )

    def test_adr_mentions_stack(self) -> None:
        content = (self._root / GENERATED_ADR).read_text()
        assert "rust" in content.lower()

    def test_adr_has_generated_from(self) -> None:
        adrs = find_adrs((self._root / GENERATED_ADR).parent)
        assert adrs[0].generated_from == "init"

    def test_ci_workflow_content(self) -> None:
        content = (self._root / ".github" / "workflows" / "ci.yml").read_text()
        assert "mise run ci" in content
        assert "mise run verify" in content
        assert "upload-artifact" in content

    def test_spec_md_exists(self) -> None:
        assert (self._root / "SPEC.md").exists()

    def test_spec_md_has_required_sections(self) -> None:
        sections = parse_sections(self._root / "SPEC.md")
        for name in SPEC_REQUIRED_SECTIONS:
            assert find_section(sections, name, level=2) is not None, (
                f"Generated SPEC.md missing section '{name}'"
            )

    def test_retired_plan_templates_are_not_generated(self) -> None:
        assert not (self._root / ".ai" / "plans").exists()

    def test_readme_dev_command_no_module(self) -> None:
        content = (self._root / "README.md").read_text()
        assert "mise run dev" in content
        assert "mise run dev -- api" not in content

    def test_agent_skills_generated(self) -> None:
        assert (self._root / ".agent" / "skills" / "README.md").exists()
        assert (
            self._root / ".agent" / "skills" / "example-skill" / "SKILL.md"
        ).exists()

    def test_scaffold_artifacts_removed(self) -> None:
        assert not (self._root / "stacks").exists()
        assert not (self._root / "templates").exists()


# ── Rust Apps ─────────────────────────────────────────────────────────────


class TestRustAppsGolden:
    @pytest.fixture(autouse=True)
    def project(self, tmp_path: Path) -> None:
        self._root = _init(
            _scaffold_copy(tmp_path),
            shape="apps",
            stack="rust",
            modules=["svc-a", "svc-b"],
        )

    def test_workspace_toml(self) -> None:
        content = (self._root / "workspace.toml").read_text()
        assert "[modules.svc-a]" in content
        assert "[modules.svc-b]" in content

    def test_per_module_cargo_toml(self) -> None:
        for mod in ["svc-a", "svc-b"]:
            cargo = self._root / "apps" / mod / "Cargo.toml"
            assert cargo.exists(), f"Missing Cargo.toml for {mod}"

    def test_gitignore_exists(self) -> None:
        assert (self._root / ".gitignore").exists()

    def test_agents_md_no_frontmatter(self) -> None:
        content = (self._root / "AGENTS.md").read_text()
        assert not content.startswith("---\n"), "AGENTS.md should not have frontmatter"

    def test_architecture_doc_has_frontmatter(self) -> None:
        content = (self._root / GENERATED_ARCHITECTURE).read_text()
        assert content.startswith("---\n"), "architecture.md missing frontmatter"
        assert "id:" in content

    def test_adr_has_frontmatter(self) -> None:
        content = (self._root / GENERATED_ADR).read_text()
        assert content.startswith("---\n"), "ADR missing frontmatter"
        assert "id:" in content

    def test_architecture_has_required_sections(self) -> None:
        sections = parse_sections(self._root / GENERATED_ARCHITECTURE)
        for name in ARCHITECTURE_REQUIRED_SECTIONS:
            assert find_section(sections, name, level=2) is not None, (
                f"Generated architecture.md missing section '{name}'"
            )

    def test_adr_schema_valid(self) -> None:
        adrs = find_adrs((self._root / GENERATED_ADR).parent)
        assert len(adrs) >= 1
        for adr in adrs:
            errors = validate_adr(adr)
            assert not errors, f"ADR {adr.filename} errors: {'; '.join(errors)}"

    def test_spec_md_exists(self) -> None:
        assert (self._root / "SPEC.md").exists()

    def test_spec_md_has_required_sections(self) -> None:
        sections = parse_sections(self._root / "SPEC.md")
        for name in SPEC_REQUIRED_SECTIONS:
            assert find_section(sections, name, level=2) is not None, (
                f"Generated SPEC.md missing section '{name}'"
            )

    def test_retired_plan_templates_are_not_generated(self) -> None:
        assert not (self._root / ".ai" / "plans").exists()

    def test_readme_dev_command_shows_module(self) -> None:
        content = (self._root / "README.md").read_text()
        assert "mise run dev -- <module>" in content

    def test_agents_md_documents_verification_contract(self) -> None:
        content = (self._root / "AGENTS.md").read_text()
        assert "scripts/verify-routes --path" in content
        assert "mise run plan" not in content

    def test_ci_workflow_apps_artifacts(self) -> None:
        content = (self._root / ".github" / "workflows" / "ci.yml").read_text()
        assert "apps/*/test-results/" in content

    def test_scaffold_artifacts_removed(self) -> None:
        assert not (self._root / "stacks").exists()
        assert not (self._root / "templates").exists()

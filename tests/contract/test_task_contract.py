"""Verify the scaffold exposes the full task contract.

These tests run on the scaffold itself (before any init) and are fast —
no subprocess invocations, just file-system assertions.
"""

from __future__ import annotations

import os

import pytest

from tests._support import SCAFFOLD_ROOT

pytestmark = pytest.mark.contract

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

TASKS_DIR = SCAFFOLD_ROOT / ".mise" / "tasks"


@pytest.mark.parametrize("task", CONTRACT_TASKS)
def test_task_file_exists(task: str) -> None:
    """Every contract task must have a file in .mise/tasks/."""
    assert (TASKS_DIR / task).exists(), f"Missing task file: .mise/tasks/{task}"


@pytest.mark.parametrize("task", CONTRACT_TASKS)
def test_task_file_is_executable(task: str) -> None:
    """Every task file must be executable."""
    assert os.access(TASKS_DIR / task, os.X_OK), (
        f"Task not executable: .mise/tasks/{task}"
    )


@pytest.mark.parametrize("task", CONTRACT_TASKS)
def test_task_has_mise_description(task: str) -> None:
    """Every task file should declare a MISE description header."""
    content = (TASKS_DIR / task).read_text()
    has_header = "#MISE description=" in content or "# MISE description=" in content
    assert has_header, f".mise/tasks/{task} is missing a MISE description header"


UV_NO_CONFIG_TASKS = {
    "setup",
    "fmt",
    "lint",
    "typecheck",
    "test",
    "build",
    "dev",
    "verify",
}


@pytest.mark.parametrize("task", CONTRACT_TASKS)
def test_task_uses_uv_shebang(task: str) -> None:
    """All task files must use the uv-managed Python shebang."""
    first_line = (TASKS_DIR / task).read_text().splitlines()[0]
    expected = (
        "#!/usr/bin/env -S env UV_NO_CONFIG=1 uv run python"
        if task in UV_NO_CONFIG_TASKS
        else "#!/usr/bin/env -S uv run python"
    )
    assert first_line == expected, (
        f".mise/tasks/{task}: expected shebang {expected!r}, got: {first_line!r}"
    )


def test_mise_toml_exists() -> None:
    assert (SCAFFOLD_ROOT / ".mise.toml").exists()


def test_scripts_lib_py_exists() -> None:
    assert (SCAFFOLD_ROOT / "scripts" / "lib.py").exists()


def test_cli_package_exists() -> None:
    assert (SCAFFOLD_ROOT / "src" / "harness_toolkit" / "__init__.py").exists()


def test_cli_entry_points_registered() -> None:
    """Harness Toolkit entry points must be declared without legacy aliases."""
    content = (SCAFFOLD_ROOT / "pyproject.toml").read_text()
    assert 'harness-scaffold = "harness_toolkit.scaffold.cli:main"' in content
    assert 'harness-kit = "harness_toolkit.kit.cli:main"' in content
    assert 'hk = "harness_toolkit.kit.cli:main"' in content
    assert "agent-scaffold" not in content
    assert "agent-workflow" not in content


def test_stacks_python_exists() -> None:
    assert (SCAFFOLD_ROOT / "stacks" / "python").is_dir()


def test_stacks_go_exists() -> None:
    assert (SCAFFOLD_ROOT / "stacks" / "go").is_dir()


def test_stacks_rust_exists() -> None:
    assert (SCAFFOLD_ROOT / "stacks" / "rust").is_dir()


def test_stacks_web_exists() -> None:
    assert (SCAFFOLD_ROOT / "stacks" / "web").is_dir()


def test_ci_workflow_exists() -> None:
    assert (SCAFFOLD_ROOT / ".github" / "workflows" / "ci.yml").exists()


def test_ci_workflow_calls_mise_ci() -> None:
    """The CI workflow must use 'mise run ci' for its quality gate."""
    workflow = (SCAFFOLD_ROOT / ".github" / "workflows" / "ci.yml").read_text()
    assert "mise run ci" in workflow


def test_ci_workflow_runs_sync_check_and_stack_smokes() -> None:
    """Repository CI must enforce handoff checks and smoke every supported stack."""
    workflow = (SCAFFOLD_ROOT / ".github" / "workflows" / "ci.yml").read_text()
    assert "name: Sync Contract" in workflow
    assert "mise run sync-check" in workflow
    assert "--changed-plans" in workflow
    assert "--changed-hk-exports" in workflow
    assert "fetch-depth: 0" in workflow
    assert "stack: python" in workflow
    assert "stack: go" in workflow
    assert "stack: rust" in workflow
    assert "stack: web" in workflow


def test_pre_commit_config_exists() -> None:
    assert (SCAFFOLD_ROOT / ".pre-commit-config.yaml").exists()


def test_pre_commit_calls_mise_tasks() -> None:
    """Pre-commit hooks must delegate to mise tasks, not raw tools."""
    content = (SCAFFOLD_ROOT / ".pre-commit-config.yaml").read_text()
    assert "mise run" in content


@pytest.mark.parametrize(
    "path",
    [
        ".gitignore",
        "templates/single/.gitignore.python.tmpl",
        "templates/single/.gitignore.go.tmpl",
        "templates/single/.gitignore.rust.tmpl",
        "templates/single/.gitignore.web.tmpl",
        "templates/apps/.gitignore.tmpl",
    ],
)
def test_gitignore_keeps_agent_scratch_out_of_git(path: str) -> None:
    """Root and generated projects should ignore local agent/harness scratch."""
    content = (SCAFFOLD_ROOT / path).read_text()
    for pattern in [
        ".ai/handoffs/",
        ".ai/research/",
        ".ai/plans/**/artifacts/**",
        "!.ai/plans/**/artifacts/manifest.yaml",
        "!.ai/plans/**/artifacts/*.md",
        "!.ai/plans/**/artifacts/*.txt",
        "!.ai/plans/**/artifacts/*.log",
        "!.ai/plans/**/artifacts/*.png",
        ".claude/settings.local.json",
        ".codex/hooks.json",
    ]:
        assert pattern in content


def test_python_stack_has_pyproject_template() -> None:
    assert (SCAFFOLD_ROOT / "stacks" / "python" / "pyproject.toml.tmpl").exists()


def test_go_stack_has_go_mod_template() -> None:
    assert (SCAFFOLD_ROOT / "stacks" / "go" / "go.mod.tmpl").exists()


def test_rust_stack_has_cargo_toml_template() -> None:
    assert (SCAFFOLD_ROOT / "stacks" / "rust" / "Cargo.toml.tmpl").exists()


def test_web_stack_has_package_and_wrangler_templates() -> None:
    project = SCAFFOLD_ROOT / "stacks" / "web" / "project"
    assert (project / "package.json.tmpl").exists()
    assert (project / "wrangler.jsonc.tmpl").exists()
    assert (project / "worker" / "index.ts").exists()
    assert (project / "migrations" / "0001_auth_and_saved_runs.sql").exists()


def test_go_stack_has_golangci_config() -> None:
    assert (SCAFFOLD_ROOT / "stacks" / "go" / ".golangci.yml").exists()


def test_golangci_config_is_v2() -> None:
    """golangci-lint v2 requires version: "2" at the top."""
    content = (SCAFFOLD_ROOT / "stacks" / "go" / ".golangci.yml").read_text()
    assert 'version: "2"' in content


def test_readme_template_exists() -> None:
    assert (SCAFFOLD_ROOT / "templates" / "README.md.tmpl").exists()


def test_agents_md_template_exists() -> None:
    assert (SCAFFOLD_ROOT / "templates" / "AGENTS.md.tmpl").exists()


def test_architecture_template_exists() -> None:
    assert (
        SCAFFOLD_ROOT / "templates" / "docs" / "explanation" / "architecture.md.tmpl"
    ).exists()


def test_adr_template_exists() -> None:
    assert (
        SCAFFOLD_ROOT
        / "templates"
        / "docs"
        / "explanation"
        / "decisions"
        / "0001-stack-choice.md.tmpl"
    ).exists()


def test_agent_skills_template_exists() -> None:
    assert (SCAFFOLD_ROOT / "templates" / ".agent" / "skills" / "README.md").exists()


def test_agent_skills_has_example_skill() -> None:
    """Skills template must include an example-skill starter with SKILL.md."""
    assert (
        SCAFFOLD_ROOT / "templates" / ".agent" / "skills" / "example-skill" / "SKILL.md"
    ).exists()


def test_agent_skills_has_slice_workflow_skill() -> None:
    """Skills template must include the canonical slice workflow skill."""
    assert (
        SCAFFOLD_ROOT
        / "templates"
        / ".agent"
        / "skills"
        / "slice-workflow"
        / "SKILL.md"
    ).exists()


def test_slice_workflow_has_holdout_tasks_reference() -> None:
    """Prompt-quality fixtures should ship with the workflow skill."""
    assert (
        SCAFFOLD_ROOT
        / "templates"
        / ".agent"
        / "skills"
        / "slice-workflow"
        / "references"
        / "holdout-sample-tasks.md"
    ).exists()


def test_slice_workflow_skill_has_uv_cli_project() -> None:
    """slice-workflow owns the Python execution layer behind the mise tasks."""
    cli_dir = (
        SCAFFOLD_ROOT / "templates" / ".agent" / "skills" / "slice-workflow" / "cli"
    )
    assert (cli_dir / "pyproject.toml").exists()
    assert (cli_dir / "src" / "slice_workflow_cli" / "cli.py").exists()
    assert (cli_dir / "src" / "slice_workflow_cli" / "__main__.py").exists()

    pyproject = (cli_dir / "pyproject.toml").read_text()
    assert 'slice-workflow = "slice_workflow_cli.cli:main"' in pyproject


@pytest.mark.parametrize(
    "task",
    [
        "plan",
        "plan-check",
        "spec-check",
        "evidence-check",
        "review-check",
        "sync-check",
        "slice-plan",
        "slice-implement",
        "slice-review",
        "slice-status",
    ],
)
def test_slice_workflow_tasks_delegate_to_skill_cli(task: str) -> None:
    """Workflow tasks should call the skill-local CLI, not repo-local helpers."""
    content = (TASKS_DIR / task).read_text()
    assert "slice-workflow" in content
    assert ".agent/skills/slice-workflow/cli" in content
    assert "templates/.agent/skills/slice-workflow/cli" in content
    assert "scripts.plan_contract" not in content
    assert "scripts.slice_workflow" not in content
    assert "from plan_contract import" not in content


def test_python_quality_tasks_include_slice_workflow_cli() -> None:
    """Scaffold Python quality gates should include the template skill CLI."""
    lint = (TASKS_DIR / "lint").read_text()
    fmt = (TASKS_DIR / "fmt").read_text()

    assert "slice-workflow/cli/src" in lint
    assert "slice-workflow/cli/src" in fmt


def test_ci_template_exists() -> None:
    assert (
        SCAFFOLD_ROOT / "templates" / ".github" / "workflows" / "ci.yml.tmpl"
    ).exists()


def test_ci_template_is_two_tier() -> None:
    """Generated CI template must include check, sync, and verify jobs."""
    content = (
        SCAFFOLD_ROOT / "templates" / ".github" / "workflows" / "ci.yml.tmpl"
    ).read_text()
    assert "mise run ci" in content
    assert "mise run sync-check" in content
    assert "--changed-plans" in content
    assert "fetch-depth: 0" in content
    assert "mise run verify" in content
    assert "upload-artifact" in content


def test_python_stack_has_test_docs_template() -> None:
    assert (
        SCAFFOLD_ROOT / "stacks" / "python" / "tests" / "test_docs.py.tmpl"
    ).exists()


# ── Plan templates ───────────────────────────────────────────────────────


def test_plan_templates_agents_md_exists() -> None:
    """Plans routing index must exist in templates."""
    assert (SCAFFOLD_ROOT / "templates" / ".ai" / "plans" / "AGENTS.md").exists()


def test_plan_templates_dir_exists() -> None:
    """Plan file templates directory must exist."""
    assert (SCAFFOLD_ROOT / "templates" / ".ai" / "plans" / "_templates").is_dir()


@pytest.mark.parametrize(
    "filename",
    [
        "META.yaml",
        "TODO.md",
        "LEARNING_LOG.md",
        "VALIDATION.md",
        "REVIEW.md",
        "DECISIONS.md",
        "artifacts/manifest.yaml",
    ],
)
def test_plan_template_required_file_exists(filename: str) -> None:
    """Every required plan template file must exist."""
    assert (
        SCAFFOLD_ROOT / "templates" / ".ai" / "plans" / "_templates" / filename
    ).exists(), f"Missing plan template: _templates/{filename}"


def test_plan_example_dir_exists() -> None:
    """Example plan directory must exist in templates."""
    assert (SCAFFOLD_ROOT / "templates" / ".ai" / "plans" / "_example").is_dir()


@pytest.mark.parametrize(
    "filename",
    [
        "META.yaml",
        "TODO.md",
        "LEARNING_LOG.md",
        "VALIDATION.md",
        "REVIEW.md",
        "DECISIONS.md",
        "artifacts/manifest.yaml",
    ],
)
def test_plan_example_has_required_file(filename: str) -> None:
    """Example plan must include all required files."""
    assert (
        SCAFFOLD_ROOT / "templates" / ".ai" / "plans" / "_example" / filename
    ).exists(), f"Example plan missing: {filename}"

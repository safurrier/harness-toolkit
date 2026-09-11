"""Fast structural checks for the generated scaffold task contract."""

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
    "dev",
    "ci",
    "verify",
    "docs",
]
TASKS_DIR = SCAFFOLD_ROOT / ".mise" / "tasks"


@pytest.mark.parametrize("task", CONTRACT_TASKS)
def test_task_file_exists_and_is_executable(task: str) -> None:
    path = TASKS_DIR / task
    assert path.exists() and os.access(path, os.X_OK)
    assert "MISE description=" in path.read_text()


def test_legacy_plan_tasks_are_not_contract_tasks() -> None:
    for task in [
        "plan",
        "plan-check",
        "spec-check",
        "evidence-check",
        "review-check",
        "slice-plan",
        "slice-implement",
        "slice-review",
        "slice-status",
    ]:
        assert not (TASKS_DIR / task).exists()


def test_verification_route_contract_exists() -> None:
    assert (SCAFFOLD_ROOT / ".harness" / "verification.toml").exists()
    runner = SCAFFOLD_ROOT / "scripts" / "verify-routes"
    assert runner.exists() and os.access(runner, os.X_OK)


def test_generated_skills_include_verification_lifecycle() -> None:
    skills = SCAFFOLD_ROOT / "templates" / ".agent" / "skills"
    for name in ["create-project-verification", "maintain-project-verification"]:
        assert (skills / name / "SKILL.md").exists()
    assert not (skills / "slice-workflow").exists()


def test_generated_ci_selects_changed_verification_routes() -> None:
    content = (
        SCAFFOLD_ROOT / "templates" / ".github" / "workflows" / "ci.yml.tmpl"
    ).read_text()
    assert "--changed-from" in content and "mise run verify" in content
    assert "changed-plans" not in content and "sync-check" not in content


def test_no_legacy_slice_source_paths_in_quality_config() -> None:
    assert "slice-workflow" not in (SCAFFOLD_ROOT / "pyproject.toml").read_text()


@pytest.mark.parametrize(
    "path",
    [
        "templates/README.md.tmpl",
        "templates/.agent/skills/README.md",
        "templates/docs/explanation/architecture.md.tmpl",
        "templates/docs/AGENTS.md.tmpl",
        "templates/docs/explanation/decision-ledger.md.tmpl",
        "templates/docs/reference/review-rubrics/README.md.tmpl",
    ],
)
def test_generated_guidance_does_not_prescribe_retired_plan_contract(path: str) -> None:
    content = (SCAFFOLD_ROOT / path).read_text()
    for retired_surface in [
        "mise run plan",
        "mise run plan-check",
        "mise run spec-check",
        "mise run evidence-check",
        "mise run review-check",
        "mise run sync-check",
        "mise run slice-plan",
        "mise run slice-implement",
        "mise run slice-review",
        "mise run slice-status",
        "META.yaml",
        "artifacts/manifest.yaml",
    ]:
        assert retired_surface not in content, f"{path} prescribes {retired_surface}"

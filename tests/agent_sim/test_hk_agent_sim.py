from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, cast

import pytest

from tests.support.hk2_repo import git_env, git_init, run_hk

pytestmark = pytest.mark.agent_sim


@pytest.fixture(autouse=True)
def isolate_harness_kit_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep agent simulations independent from developer HK target bindings."""
    config = tmp_path / "harness.toml"
    config.write_text('version = 1\ndefault_profile = "generic"\n')
    monkeypatch.setenv("HARNESS_KIT_CONFIG", str(config))


def _json(result) -> dict[str, object]:
    assert result.returncode == 0, (result.stdout, result.stderr)
    return json.loads(result.stdout)


def test_agent_sim_happy_path_reaches_ready_through_public_cli(tmp_path: Path) -> None:
    target = git_init(tmp_path / "repo")

    start = _json(
        run_hk(
            "start",
            "agent-sim-happy-path",
            "--plan",
            "Exercise the public HK lifecycle like an implementation agent.",
            "--target",
            str(target),
            "--json",
        )
    )
    assert start["work_id"]

    context = _json(
        run_hk(
            "context",
            "Fixture repo uses README.md as the changed file.",
            "--target",
            str(target),
            "--json",
        )
    )
    assert context["kind"] == "context"

    (target / "README.md").write_text("# demo\n\nAgent simulation touched this file.\n")

    decision = _json(
        run_hk(
            "decide",
            "README-only fixture change has no product spec impact.",
            "--spec-impact",
            "not-needed",
            "--target",
            str(target),
            "--json",
        )
    )
    assert decision["kind"] == "decision"

    validation = _json(
        run_hk(
            "validate",
            "--why",
            "Native command evidence proves the agent simulation command path works.",
            "--target",
            str(target),
            "--json",
            "--",
            "python3",
            "-c",
            "print('agent sim ok')",
        )
    )
    assert validation["status"] == "pass"

    review = _json(
        run_hk(
            "review",
            "add",
            "--backend",
            "subagent",
            "--reviewer",
            "reviewer-fresh-context",
            "--summary",
            "No blockers for happy-path simulation.",
            "--target",
            str(target),
            "--json",
        )
    )
    assert review["reviewer"] == "reviewer-fresh-context"

    sync = _json(run_hk("sync", "--target", str(target), "--json"))
    assert sync["synced"] is True

    status = _json(run_hk("status", "--target", str(target), "--json"))
    assert status["ready_status"] == "ready"
    next_actions = status["next_actions"]
    assert isinstance(next_actions, list)
    assert "handoff: hk handoff" in next_actions

    ready = _json(run_hk("ready", "--target", str(target), "--json"))
    assert ready["ready"] is True
    assert ready["status"] == "ready"

    summary = run_hk("summary", "--target", str(target))
    assert summary.returncode == 0, summary.stderr
    assert "- Readiness: `ready`" in summary.stdout

    handoff = run_hk("handoff", "--target", str(target))
    assert handoff.returncode == 0, handoff.stderr
    assert "## Validation evidence" in handoff.stdout
    assert "## Review" in handoff.stdout


def test_agent_sim_profile_resolution_follows_git_linked_worktree(
    tmp_path: Path,
) -> None:
    repo = git_init(tmp_path / "repo")
    module = repo / "module"
    module.mkdir()
    (module / "README.md").write_text("# module\n")
    subprocess.run(
        ["git", "add", "module/README.md"],
        cwd=repo,
        check=True,
        capture_output=True,
        env=git_env(),
    )
    subprocess.run(
        ["git", "commit", "--no-verify", "-m", "test: add module"],
        cwd=repo,
        check=True,
        capture_output=True,
        env=git_env(),
    )
    worktree = tmp_path / "agent-worktree"
    subprocess.run(
        ["git", "worktree", "add", "--detach", str(worktree), "HEAD"],
        cwd=repo,
        check=True,
        capture_output=True,
        env=git_env(),
    )
    config = tmp_path / "harness.toml"
    config.write_text(
        f'''
version = 1

[[targets]]
name = "repo"
path = "{repo}"
profile = "repo-profile"

[[targets]]
name = "module"
path = "{module}"
profile = "module-profile"

[profiles.repo-profile]
title = "Repo"
summary = "Repo profile."
target_hint = "repo"
instructions = "repo instructions"

[[profiles.repo-profile.checks]]
name = "repo-check"
purpose = "Repo check."
command_template = "repo-check"
run_from = "repo-root"

[profiles.module-profile]
title = "Module"
summary = "Module profile."
target_hint = "module"
instructions = "module instructions"

[[profiles.module-profile.checks]]
name = "module-check"
purpose = "Module check."
command_template = "module-check"
run_from = "target"
'''
    )

    resolved = _json(
        run_hk(
            "profile",
            "resolve",
            "--target",
            str(worktree / "module"),
            "--json",
            env={"HARNESS_KIT_CONFIG": str(config)},
        )
    )

    assert resolved["profile"] == "module-profile"
    assert resolved["matched_name"] == "module"
    assert resolved["matched_target"] == str(module)
    assert resolved["worktree_projected_target"] == str((worktree / "module").resolve())


def test_agent_sim_attaches_tool_transcript_and_exports_handoff(
    tmp_path: Path,
) -> None:
    target = git_init(tmp_path / "repo")
    transcript = tmp_path / "codex-review-events.jsonl"
    transcript.write_text('{"event":"review","message":"No blockers"}\n')
    summary = tmp_path / "codex-review-last.md"
    summary.write_text("# Codex review\nNo blockers.\n")

    _json(
        run_hk(
            "start",
            "agent-artifact-attach",
            "--plan",
            "Attach tool-produced transcript evidence before handoff.",
            "--target",
            str(target),
            "--json",
        )
    )
    (target / "README.md").write_text(
        "# demo\n\nArtifact simulation touched this file.\n"
    )
    _json(
        run_hk(
            "decide",
            "Artifact attachment changes no product spec.",
            "--spec-impact",
            "not-needed",
            "--target",
            str(target),
            "--json",
        )
    )
    attached = _json(
        run_hk(
            "artifact",
            "attach",
            "--path",
            str(transcript),
            "--kind",
            "codex-review-transcript",
            "--label",
            "Codex review JSONL",
            "--redaction",
            "external",
            "--target",
            str(target),
            "--json",
        )
    )
    _json(
        run_hk(
            "artifact",
            "attach",
            "--path",
            str(summary),
            "--kind",
            "codex-review-summary",
            "--label",
            "Codex review final message",
            "--redaction",
            "external",
            "--target",
            str(target),
            "--json",
        )
    )
    listed = _json(run_hk("artifact", "list", "--target", str(target), "--json"))
    artifacts = listed["artifacts"]
    assert isinstance(artifacts, list)
    artifact_rows = cast("list[dict[str, Any]]", artifacts)
    assert [item["kind"] for item in artifact_rows] == [
        "codex-review-transcript",
        "codex-review-summary",
    ]
    assert attached["copied"] is True

    _json(
        run_hk(
            "validate",
            "--why",
            "Native validation command path still works with attached artifacts.",
            "--target",
            str(target),
            "--json",
            "--",
            "python3",
            "-c",
            "print('artifact workflow ok')",
        )
    )
    _json(
        run_hk(
            "review",
            "add",
            "--backend",
            "codex-cli",
            "--reviewer",
            "fresh-context-reviewer",
            "--summary",
            "Transcript attachment workflow is understandable.",
            "--target",
            str(target),
            "--json",
        )
    )
    _json(run_hk("sync", "--target", str(target), "--json"))
    ready = _json(run_hk("ready", "--target", str(target), "--json"))
    assert ready["ready"] is True

    export_dir = tmp_path / "export"
    exported = _json(
        run_hk(
            "export",
            "--format",
            "handoff-dir",
            "--output",
            str(export_dir),
            "--target",
            str(target),
            "--json",
        )
    )
    assert exported["fresh"] is True
    metadata = json.loads((export_dir / "meta.json").read_text())
    export_paths = [item["export_path"] for item in metadata["attached_artifacts"]]
    assert all(path in metadata["files"] for path in export_paths)
    assert all((export_dir / path).exists() for path in export_paths)
    assert "Codex review JSONL" in (export_dir / "README.md").read_text()


def test_agent_sim_validation_and_review_go_stale_after_diff_changes(
    tmp_path: Path,
) -> None:
    target = git_init(tmp_path / "repo")
    _json(
        run_hk(
            "start",
            "agent-stale-review",
            "--plan",
            "Exercise validation/review freshness.",
            "--target",
            str(target),
            "--json",
        )
    )
    (target / "README.md").write_text("# v1\n")
    _json(
        run_hk(
            "decide",
            "README fixture has no spec impact.",
            "--spec-impact",
            "not-needed",
            "--target",
            str(target),
            "--json",
        )
    )
    _json(
        run_hk(
            "validate",
            "--why",
            "Validation covers v1.",
            "--target",
            str(target),
            "--json",
            "--",
            "python3",
            "-c",
            "print('ok')",
        )
    )
    _json(
        run_hk(
            "review",
            "add",
            "--backend",
            "subagent",
            "--reviewer",
            "reviewer-fresh-context",
            "--summary",
            "Review covers v1.",
            "--target",
            str(target),
            "--json",
        )
    )

    (target / "README.md").write_text("# v2\n")
    _json(run_hk("sync", "--target", str(target), "--json"))
    ready = run_hk("ready", "--target", str(target), "--json")

    assert ready.returncode == 1
    payload = json.loads(ready.stdout)
    assert payload["ready"] is False
    messages = {check["id"]: check["message"] for check in payload["checks"]}
    assert "validation evidence is stale" in messages["validation"]
    assert "does not cover current changed paths" in messages["review"]
    assert "targeted follow-up" in messages["review"]


def test_agent_sim_local_state_churn_stales_sync_exclusion(tmp_path: Path) -> None:
    target = git_init(tmp_path / "repo")
    _json(
        run_hk(
            "start",
            "agent-local-churn",
            "--plan",
            "Exercise excluded agent-local state freshness.",
            "--target",
            str(target),
            "--json",
        )
    )
    local_state = target / ".pi" / "session.json"
    local_state.parent.mkdir()
    local_state.write_text("{}\n")

    sync = _json(
        run_hk(
            "sync",
            "--exclude",
            ".pi",
            "--reason",
            "Only local agent state.",
            "--target",
            str(target),
            "--json",
        )
    )
    assert sync["synced"] is True

    local_state.write_text('{"changed": true}\n')
    checked = run_hk("sync", "--check", "--target", str(target), "--json")

    assert checked.returncode == 1
    payload = json.loads(checked.stdout)
    assert payload["synced"] is False
    assert "excluded path changed" in payload["message"]

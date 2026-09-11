"""Harness Kit local assistant primitives.

This module intentionally keeps the first lifecycle implementation small: repo brief,
local/external state, ledger-backed work units, sync checkpoints, command
capture, generated handoff/materialized views, and local specs.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import shutil
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from harness_toolkit.kit.capture.process import run_process_to_transcript
from harness_toolkit.kit.capture.redaction import redact_argv, redact_text
from harness_toolkit.kit.capture.transcripts import transcript_path
from harness_toolkit.kit.git import snapshot as git_snapshot
from harness_toolkit.kit.git.client import DEFAULT_GIT_CLIENT
from harness_toolkit.kit.handoff.export import (
    HandoffExportError,
    prepare_generated_directory,
    reject_symlink_ancestors,
    safe_copy_generated_file,
    safe_write_generated_file,
)
from harness_toolkit.kit.ledger import lifecycle_events
from harness_toolkit.kit.ledger.events import append_lifecycle_event
from harness_toolkit.kit.ledger.models import EventRecord, EvidenceRecord
from harness_toolkit.kit.ledger.store import (
    LedgerStoreError,
)
from harness_toolkit.kit.ledger.store import (
    next_seq as ledger_next_seq,
)
from harness_toolkit.kit.ledger.store import (
    read_events as ledger_read_events,
)
from harness_toolkit.kit.ledger.store import (
    read_evidence as ledger_read_evidence,
)
from harness_toolkit.kit.profiles import (
    ProfileError,
    ProfileSuggestion,
    load_profile_catalog,
    profile_names,
    resolve_profile,
    resolve_target_system_map,
)
from harness_toolkit.kit.profiles.context import ProfileContext
from harness_toolkit.kit.readiness.diagnostics import ReadyCheck, ReadyResult
from harness_toolkit.kit.readiness.policy import (
    SELF_REVIEW_GUIDANCE,
    RequiredProfileItem,
    dangerous_skip_events,
    dangerous_skip_message,
    is_self_review_identity,
    notes_by_kind,
    notes_by_kinds,
    ready_for_events,
)
from harness_toolkit.kit.readiness.policy import (
    lifecycle_phase as policy_lifecycle_phase,
)
from harness_toolkit.kit.readiness.status import (
    EvidenceFreshnessItem,
    ExportFreshnessNote,
    build_evidence_freshness_items,
    build_export_freshness_note,
)
from harness_toolkit.kit.rendering.handoff import (
    render_handoff_markdown,
    render_handoff_pr_markdown,
    render_summary_markdown,
)
from harness_toolkit.kit.rendering.materialize import write_note_views
from harness_toolkit.kit.rendering.review_prompt import render_review_prompt
from harness_toolkit.kit.specs.models import SpecOutline, SpecResult
from harness_toolkit.kit.specs.operations import (
    SpecWorkflowError,
    find_specs_for_state,
    init_spec_for_state,
    spec_outline_for_state,
    spec_promote_dry_run_for_state,
    spec_status_for_state,
)
from harness_toolkit.kit.state.repo import (
    RepoStateError,
    git_branch,
    git_root,
    repo_key,
)
from harness_toolkit.kit.state.repo import (
    scope_key as repo_scope_key,
)
from harness_toolkit.kit.sync import freshness as sync_freshness
from harness_toolkit.kit.system_map import (
    SystemMapSummary,
    load_system_map,
    summary_from_load_result,
)

LOCAL_STATE_DIR = ".harness-local"
KIT_STATE_DIR = "harness-kit"
STATE_SCHEMA_VERSION = 1
WORK_DIR_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-\d{6}-")
VALID_NOTE_KINDS = (
    "context",
    "plan",
    "background",
    "learning",
    "decision",
    "gap",
    "spec-impact",
)
VALID_EVIDENCE_KINDS = ("test", "lint", "typecheck", "build", "check", "e2e", "other")
SYNC_IGNORED_EVENT_TYPES = frozenset(
    {"sync_checkpoint", "view_materialized", "handoff_generated"}
)
COMMON_AGENT_LOCAL_STATE_PATHS = (".pi", ".claude/worktrees")
VALIDATION_FRESHNESS_EXCLUDES: tuple[str, ...] = ()
StateMode = Literal["local", "external"]
NoteKind = Literal[
    "context", "plan", "background", "learning", "decision", "gap", "spec-impact"
]
EvidenceKind = Literal["test", "lint", "typecheck", "build", "check", "e2e", "other"]
HandoffFormat = Literal["markdown", "pr"]


class LocalWorkflowError(RuntimeError):
    """Expected local assistant failure shown without traceback."""


@dataclass(frozen=True)
class LocalState:
    target_root: Path
    target_scope: Path
    state_dir: Path
    mode: StateMode
    scope: str
    repo_key: str


@dataclass(frozen=True)
class GitInfo:
    available: bool
    worktree_root: str | None = None
    git_dir: str | None = None
    git_common_dir: str | None = None
    is_linked_worktree: bool = False


@dataclass(frozen=True)
class HandoffExportStatus:
    work_id: str | None
    format: str
    state: str
    exists: bool
    fresh: bool
    path: str | None = None
    relative_path: str | None = None
    readme_path: str | None = None
    meta_path: str | None = None
    readme_exists: bool = False
    checked: bool = True
    message: str = ""
    stale_reasons: list[str] | None = None
    commands: dict[str, str] | None = None


@dataclass(frozen=True)
class Brief:
    target_root: str
    target_scope: str
    branch: str
    git_sha: str
    dirty: bool
    state_dir: str
    state_exists: bool
    active_work: str
    sync_status: str
    agents_md: list[str]
    spec_sources: list[str]
    repo_surfaces: list[str]
    profiles: list[str]
    system_map: SystemMapSummary | None
    git: GitInfo
    handoff_export: HandoffExportStatus


@dataclass(frozen=True)
class InitResult:
    target_root: str
    target_scope: str
    state_dir: str
    mode: str
    ignored_by_local_git: bool


@dataclass(frozen=True)
class WorkResult:
    work_id: str
    work_dir: str
    state_dir: str
    resumed: bool = False


@dataclass(frozen=True)
class NoteResult:
    work_id: str
    seq: int
    kind: str
    text: str


@dataclass(frozen=True)
class InvariantSupersessionResult:
    work_id: str
    seq: int
    invariant: str
    previous: str
    reason: str
    replacement: str = ""
    removal_rationale: str = ""
    docs: list[str] | None = None
    commit_trailer: str = ""


@dataclass(frozen=True)
class DangerousSkipResult:
    work_id: str
    seq: int
    check: str
    label: str
    reason: str
    mitigation: str


@dataclass(frozen=True)
class SyncResult:
    work_id: str
    synced: bool
    message: str
    guidance: list[str]


@dataclass(frozen=True)
class CaptureResult:
    work_id: str
    evidence_id: str
    exit_code: int
    status: str
    transcript_path: str
    why: str = ""
    check_name: str = ""
    timed_out: bool = False
    truncated: bool = False
    transcript_bytes: int = 0


@dataclass(frozen=True)
class ReviewResult:
    work_id: str
    seq: int
    backend: str
    reviewer: str
    summary: str
    disposition: str
    review_name: str = ""
    reviewed_paths: list[str] | None = None


@dataclass(frozen=True)
class StatusResult:
    active_work: str
    target_root: str
    target_scope: str
    state_dir: str
    sync_status: str
    ready_status: str
    phase: str
    checks: list[ReadyCheck]
    next_actions: list[str]
    suggested_checks: list[ProfileSuggestion] | None = None
    suggested_reviews: list[ProfileSuggestion] | None = None
    invariant_supersessions: list[dict[str, object]] | None = None
    evidence_freshness: list[EvidenceFreshnessItem] | None = None
    export_freshness: ExportFreshnessNote | None = None


@dataclass(frozen=True)
class ReviewPromptResult:
    work_id: str
    prompt: str


@dataclass(frozen=True)
class HandoffResult:
    work_id: str
    content: str
    path: str = ""


@dataclass(frozen=True)
class ExportResult:
    work_id: str
    path: str
    format: str
    checked: bool = False
    fresh: bool = True
    message: str = ""


@dataclass(frozen=True)
class ArtifactResult:
    work_id: str
    seq: int
    kind: str
    label: str
    source_path: str
    artifact_path: str
    sha256: str
    size_bytes: int
    copied: bool
    redaction: str


@dataclass(frozen=True)
class ArtifactRecord:
    seq: int
    kind: str
    label: str
    source_path: str
    artifact_path: str
    sha256: str
    size_bytes: int
    copied: bool
    redaction: str


@dataclass(frozen=True)
class ArtifactListResult:
    work_id: str
    artifacts: list[ArtifactRecord]


JsonDataclass = (
    Brief
    | InitResult
    | WorkResult
    | NoteResult
    | DangerousSkipResult
    | SyncResult
    | CaptureResult
    | ReviewResult
    | ReadyResult
    | StatusResult
    | ReviewPromptResult
    | SpecResult
    | SpecOutline
    | HandoffResult
    | ExportResult
    | HandoffExportStatus
    | ArtifactResult
    | ArtifactListResult
)


def utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def default_state_home() -> Path:
    state_home = Path(
        os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state")
    )
    return state_home / "harness-toolkit" / "repos"


def scope_key(target_root: Path, target_scope: Path) -> str:
    return repo_scope_key(target_root, target_scope)


def resolve_local_state(target: Path, *, no_local_files: bool = False) -> LocalState:
    target_scope = target.resolve()
    try:
        target_root = git_root(target_scope)
    except RepoStateError as e:
        raise LocalWorkflowError(str(e)) from e
    scope = scope_key(target_root, target_scope)
    key = repo_key(target_root)
    if no_local_files:
        state_dir = default_state_home() / key / scope
        mode: StateMode = "external"
    else:
        state_dir = target_root / LOCAL_STATE_DIR / KIT_STATE_DIR / scope
        mode = "local"
    return LocalState(
        target_root=target_root,
        target_scope=target_scope,
        state_dir=state_dir.resolve(),
        mode=mode,
        scope=scope,
        repo_key=key,
    )


def git_sha(path: Path) -> str:
    return git_snapshot.git_sha(path)


def git_dirty(path: Path) -> bool:
    return git_snapshot.git_dirty(path)


def agent_local_state_paths(path: Path) -> list[str]:
    return git_snapshot.agent_local_state_paths(path, COMMON_AGENT_LOCAL_STATE_PATHS)


def agent_local_state_warning(path: Path) -> str:
    paths = agent_local_state_paths(path)
    if not paths:
        return ""
    examples = " ".join(f"--exclude {item}" for item in paths)
    return (
        " Common agent-local state is present in git status "
        f"({', '.join(paths)}); it is blocking sync readiness. If disposable, "
        "remove or git-ignore it. If expected harness-local state, run exactly: "
        f"`hk sync {examples} --reason agent-local-state`."
    )


def git_pathspec_excludes(exclude_paths: tuple[str, ...] = ()) -> list[str]:
    return git_snapshot.git_pathspec_excludes(exclude_paths)


def git_tracked_paths_for_path(path: Path, candidate: str) -> list[str]:
    return git_snapshot.git_tracked_paths_for_path(path, candidate)


def sync_exclude_safety_error(path: Path, candidate: str) -> str:
    return git_snapshot.sync_exclude_safety_error(path, candidate)


def git_status_for_path(path: Path, candidate: str) -> str:
    return git_snapshot.git_status_for_path(path, candidate)


def git_diff_hash(path: Path, exclude_paths: tuple[str, ...] = ()) -> str:
    return git_snapshot.git_diff_hash(path, exclude_paths)


def active_handoff_export_excludes(work_dir: Path | None) -> tuple[str, ...]:
    if work_dir is None:
        return ()
    return (f".ai/hk/{work_dir.name}",)


def work_freshness_excludes(
    work_dir: Path | None, *exclude_groups: tuple[str, ...]
) -> tuple[str, ...]:
    values: list[str] = [*active_handoff_export_excludes(work_dir)]
    for group in exclude_groups:
        values.extend(group)
    return tuple(dict.fromkeys(path for path in values if path))


def git_work_diff_hash(
    path: Path, *, base_sha: str, exclude_paths: tuple[str, ...] = ()
) -> str:
    return git_snapshot.git_work_diff_hash(
        path, base_sha=base_sha, exclude_paths=exclude_paths
    )


def validation_diff_hash(
    path: Path, *, base_sha: str = "", extra_excludes: tuple[str, ...] = ()
) -> str:
    return git_snapshot.git_validation_work_diff_hash(
        path,
        base_sha=base_sha,
        exclude_paths=(*VALIDATION_FRESHNESS_EXCLUDES, *extra_excludes),
    )


def latest_sync_excluded_paths(events: list[EventRecord]) -> tuple[str, ...]:
    sync_events = [event for event in events if event.type == "sync_checkpoint"]
    if not sync_events:
        return ()
    return normalize_exclude_paths(
        string_list_from_event_data(sync_events[-1].data, "excluded_paths")
    )


def local_exclude_file(path: Path) -> Path | None:
    return DEFAULT_GIT_CLIENT.git_path(path, "info/exclude")


def ensure_local_exclude(state: LocalState) -> bool:
    if state.mode != "local":
        return False
    exclude = local_exclude_file(state.target_root)
    if exclude is None:
        return False
    exclude.parent.mkdir(parents=True, exist_ok=True)
    existing = exclude.read_text() if exclude.exists() else ""
    pattern = f"/{LOCAL_STATE_DIR}/{KIT_STATE_DIR}/"
    if pattern in existing:
        return True
    marker = f"# harness-kit 2 local state\n{pattern}\n# /harness-kit 2 local state\n"
    separator = "" if not existing or existing.endswith("\n") else "\n"
    exclude.write_text(existing + separator + marker)
    return True


def init_state(target: Path, *, no_local_files: bool = False) -> InitResult:
    state = resolve_local_state(target, no_local_files=no_local_files)
    state.state_dir.mkdir(parents=True, exist_ok=True)
    for child in ("work", "spec"):
        (state.state_dir / child).mkdir(exist_ok=True)
    metadata = {
        "schema_version": STATE_SCHEMA_VERSION,
        "target_root": str(state.target_root),
        "target_scope": str(state.target_scope),
        "state_dir": str(state.state_dir),
        "mode": state.mode,
        "scope": state.scope,
        "repo_key": state.repo_key,
        "updated_at": utc_now(),
    }
    (state.state_dir / "state.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n"
    )
    ignored = ensure_local_exclude(state)
    return InitResult(
        target_root=str(state.target_root),
        target_scope=str(state.target_scope),
        state_dir=str(state.state_dir),
        mode=state.mode,
        ignored_by_local_git=ignored,
    )


def ensure_state(target: Path, *, no_local_files: bool = False) -> LocalState:
    state = resolve_local_state(target, no_local_files=no_local_files)
    if not (state.state_dir / "state.json").exists():
        init_state(target, no_local_files=no_local_files)
    return state


def list_work_dirs(state: LocalState) -> list[Path]:
    root = state.state_dir / "work"
    if not root.is_dir():
        return []
    return sorted(
        path
        for path in root.iterdir()
        if path.is_dir() and WORK_DIR_RE.match(path.name)
    )


def active_work_dir(state: LocalState) -> Path | None:
    active = state.state_dir / "active-work"
    if active.exists():
        candidate = state.state_dir / "work" / active.read_text().strip()
        if candidate.is_dir():
            return candidate
    work = list_work_dirs(state)
    return work[-1] if work else None


def validate_slug(slug: str) -> str:
    normalized = slug.strip()
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", normalized):
        raise LocalWorkflowError(
            "Invalid slug: use lowercase letters, digits, and hyphens"
        )
    return normalized


def next_seq(events_path: Path) -> int:
    try:
        return ledger_next_seq(events_path)
    except LedgerStoreError as e:
        raise LocalWorkflowError(str(e)) from e


def append_event(
    work_dir: Path, event_type: str, data: dict[str, object]
) -> EventRecord:
    try:
        return append_lifecycle_event(
            work_dir, event_type, data, schema_version=STATE_SCHEMA_VERSION
        )
    except LedgerStoreError as e:
        raise LocalWorkflowError(str(e)) from e


def create_work(
    target: Path, slug_arg: str, *, no_local_files: bool = False
) -> WorkResult:
    slug = validate_slug(slug_arg)
    state = ensure_state(target, no_local_files=no_local_files)
    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    work_id = f"{timestamp}-{slug}"
    work_dir = state.state_dir / "work" / work_id
    if work_dir.exists():
        raise LocalWorkflowError(f"work already exists: {work_dir}")
    (work_dir / "artifacts").mkdir(parents=True)
    (work_dir / "views").mkdir()
    (work_dir / "evidence.jsonl").write_text("")
    append_event(
        work_dir,
        "work_started",
        {
            "slug": slug,
            "target_root": str(state.target_root),
            "target_scope": str(state.target_scope),
            "branch": git_branch(state.target_root),
            "git_sha": git_sha(state.target_root),
        },
    )
    (state.state_dir / "active-work").write_text(work_id + "\n")
    return WorkResult(
        work_id=work_id, work_dir=str(work_dir), state_dir=str(state.state_dir)
    )


def require_work(state: LocalState) -> Path:
    work_dir = active_work_dir(state)
    if work_dir is None:
        raise LocalWorkflowError(
            "No active work. Run `hk start demo-work --plan 'Describe the intended change'` first."
        )
    return work_dir


def add_note(
    target: Path,
    *,
    kind: str,
    text: str,
    no_local_files: bool = False,
) -> NoteResult:
    if kind not in VALID_NOTE_KINDS:
        valid = ", ".join(VALID_NOTE_KINDS)
        raise LocalWorkflowError(f"invalid note kind '{kind}'. Valid: {valid}")
    state = ensure_state(target, no_local_files=no_local_files)
    work_dir = require_work(state)
    record = append_event(work_dir, "note_added", {"kind": kind, "text": text})
    return NoteResult(work_id=work_dir.name, seq=record.seq, kind=kind, text=text)


def _repo_relative_string(path: str, repo_root: Path) -> str:
    candidate = Path(path)
    if candidate.is_absolute():
        try:
            return (
                candidate.resolve(strict=False)
                .relative_to(repo_root.resolve(strict=False))
                .as_posix()
            )
        except ValueError:
            return candidate.as_posix()
    clean = path.strip().replace("\\", "/")
    while clean.startswith("./"):
        clean = clean[2:]
    return clean.strip("/")


def add_invariant_supersession(
    target: Path,
    *,
    invariant: str,
    previous: str,
    reason: str,
    replacement: str = "",
    removal_rationale: str = "",
    docs: tuple[str, ...] = (),
    no_local_files: bool = False,
) -> InvariantSupersessionResult:
    state = ensure_state(target, no_local_files=no_local_files)
    work_dir = require_work(state)
    normalized_docs = tuple(
        dict.fromkeys(_repo_relative_string(doc, state.target_root) for doc in docs)
    )
    payload: dict[str, object] = {
        "invariant": invariant,
        "previous": previous,
        "reason": reason,
        "replacement": replacement,
        "removal_rationale": removal_rationale,
        "docs": list(normalized_docs),
    }
    record = append_event(work_dir, "invariant_superseded", payload)
    return InvariantSupersessionResult(
        work_id=work_dir.name,
        seq=record.seq,
        invariant=invariant,
        previous=previous,
        reason=reason,
        replacement=replacement,
        removal_rationale=removal_rationale,
        docs=list(normalized_docs),
        commit_trailer=f"Supersedes-Invariant: {invariant}",
    )


def read_events(work_dir: Path) -> list[EventRecord]:
    try:
        return ledger_read_events(work_dir)
    except LedgerStoreError as e:
        raise LocalWorkflowError(str(e)) from e


def read_evidence(work_dir: Path) -> list[EvidenceRecord]:
    try:
        return ledger_read_evidence(work_dir)
    except LedgerStoreError as e:
        raise LocalWorkflowError(str(e)) from e


def int_from_event_data(data: dict[str, object], key: str) -> int:
    value = data.get(key, 0)
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return int(value)
    return 0


def string_list_from_event_data(data: dict[str, object], key: str) -> tuple[str, ...]:
    value = data.get(key, [])
    if not isinstance(value, list):
        return ()
    return tuple(str(item) for item in value)


def latest_sync_relevant_seq(events: list[EventRecord]) -> int:
    return max(
        (event.seq for event in events if event.type not in SYNC_IGNORED_EVENT_TYPES),
        default=0,
    )


def normalize_exclude_paths(exclude_paths: tuple[str | Path, ...]) -> tuple[str, ...]:
    try:
        return sync_freshness.normalize_exclude_paths(exclude_paths)
    except sync_freshness.SyncFreshnessError as e:
        raise LocalWorkflowError(str(e)) from e


def git_path_state_hash(path: Path, candidate: str) -> str:
    return git_snapshot.git_path_state_hash(path, candidate)


def changed_path_hashes(path: Path, changed_paths: tuple[str, ...]) -> dict[str, str]:
    return {
        candidate: digest
        for candidate in changed_paths
        if (digest := git_snapshot.git_worktree_path_hash(path, candidate))
    }


def excluded_path_metadata(
    path: Path, exclude_paths: tuple[str, ...]
) -> list[dict[str, str]]:
    return sync_freshness.excluded_path_metadata(path, exclude_paths)


def excluded_path_state_changed(
    path: Path, recorded: object, *, expected_paths: tuple[str, ...] = ()
) -> bool:
    return sync_freshness.excluded_path_state_changed(
        path, recorded, expected_paths=expected_paths
    )


def sync_checkpoint(
    target: Path,
    *,
    check: bool = False,
    exclude_paths: tuple[str | Path, ...] = (),
    reason: str = "",
    no_local_files: bool = False,
) -> SyncResult:
    state = ensure_state(target, no_local_files=no_local_files)
    work_dir = require_work(state)
    events = read_events(work_dir)
    latest_seq = latest_sync_relevant_seq(events)
    normalized_excludes = normalize_exclude_paths(exclude_paths)
    if check and normalized_excludes:
        raise LocalWorkflowError("sync --check cannot be combined with --exclude")
    if normalized_excludes and not reason.strip():
        raise LocalWorkflowError("sync --exclude requires --reason")
    for candidate in normalized_excludes:
        if error := sync_exclude_safety_error(state.target_root, candidate):
            raise LocalWorkflowError(error)
    implicit_excludes = active_handoff_export_excludes(work_dir)
    current_hash = git_diff_hash(
        state.target_root, work_freshness_excludes(work_dir, normalized_excludes)
    )
    if not current_hash:
        raise LocalWorkflowError("could not compute git diff hash for sync checkpoint")
    sync_events = [event for event in events if event.type == "sync_checkpoint"]
    guidance = [
        "Plan: did you record the agreed implementation intent?",
        "Evidence: did you capture or explain validation?",
        "Learning: did you record anything future agents should know?",
        "Decisions: did you record non-obvious choices?",
        "Gaps: did you disclose missing validation or follow-up work?",
        "Spec/docs: did behavior or product intent change?",
    ]
    if check:
        skip = fresh_sync_skip(events, state) if sync_events else None
        if not sync_events:
            return SyncResult(
                work_id=work_dir.name,
                synced=False,
                message="needs sync: no checkpoint",
                guidance=guidance,
            )
        latest_sync = sync_events[-1]
        synced_seq = int_from_event_data(latest_sync.data, "event_seq")
        checkpoint_excludes = normalize_exclude_paths(
            string_list_from_event_data(latest_sync.data, "excluded_paths")
        )
        for candidate in checkpoint_excludes:
            if sync_exclude_safety_error(state.target_root, candidate):
                return SyncResult(
                    work_id=work_dir.name,
                    synced=False,
                    message="needs sync: excluded path changed or is no longer local-only",
                    guidance=guidance,
                )
        if checkpoint_excludes and excluded_path_state_changed(
            state.target_root,
            latest_sync.data.get("excluded"),
            expected_paths=checkpoint_excludes,
        ):
            return SyncResult(
                work_id=work_dir.name,
                synced=False,
                message="needs sync: excluded path changed or is no longer local-only",
                guidance=guidance,
            )
        synced_hash = str(latest_sync.data.get("diff_hash", ""))
        current_hash = git_diff_hash(
            state.target_root, work_freshness_excludes(work_dir, checkpoint_excludes)
        )
        if not current_hash:
            raise LocalWorkflowError("could not compute git diff hash for sync check")
        synced = synced_seq >= latest_seq and _sync_hash_matches(
            state,
            work_dir,
            synced_hash,
            checkpoint_excludes,
            implicit_recorded="implicit_excluded_paths" in latest_sync.data,
        )
        if not synced and skip is not None:
            return SyncResult(
                work_id=work_dir.name,
                synced=True,
                message=dangerous_skip_message("sync", [skip]),
                guidance=guidance,
            )
        message = "synced" if synced else "needs sync: work changed after checkpoint"
        return SyncResult(
            work_id=work_dir.name, synced=synced, message=message, guidance=guidance
        )

    evidence_count = len(read_evidence(work_dir))
    note_count = len([event for event in events if event.type == "note_added"])
    data: dict[str, object] = {
        "git_sha": git_sha(state.target_root),
        "diff_hash": current_hash,
        "event_seq": latest_seq,
        "evidence_count": evidence_count,
        "note_count": note_count,
    }
    if implicit_excludes:
        data["implicit_excluded_paths"] = list(implicit_excludes)
    if normalized_excludes:
        data.update(
            {
                "excluded_paths": list(normalized_excludes),
                "exclude_reason": reason.strip(),
                "excluded": excluded_path_metadata(
                    state.target_root, normalized_excludes
                ),
            }
        )
    append_event(work_dir, "sync_checkpoint", data)
    return SyncResult(
        work_id=work_dir.name,
        synced=True,
        message="recorded sync checkpoint",
        guidance=guidance,
    )


def command_display(command: tuple[str, ...], shell_command: str) -> str:
    if shell_command:
        return shell_command
    return " ".join(shlex.quote(part) for part in command)


def _looks_like_env_assignment(value: str) -> bool:
    name, sep, rest = value.partition("=")
    return bool(
        sep and rest and name.replace("_", "a").isalnum() and not name[0].isdigit()
    )


def capture_command(
    target: Path,
    command: tuple[str, ...],
    *,
    shell_command: str = "",
    kind: str = "other",
    why: str = "",
    check_name: str = "",
    no_log: bool = False,
    raw_log: bool = False,
    no_local_files: bool = False,
    stream_to_stderr: bool = False,
    timeout_seconds: int = 0,
    max_log_bytes: int = 0,
) -> CaptureResult:
    if not command and not shell_command:
        raise LocalWorkflowError("capture requires a command after -- or --shell TEXT")
    if command and shell_command:
        raise LocalWorkflowError(
            "capture accepts either --shell TEXT or argv after --, not both"
        )
    if command and _looks_like_env_assignment(command[0]):
        raise LocalWorkflowError(
            "captured commands run argv directly; environment assignments like "
            f"`{command[0]}` are not shell syntax here. Use `env {command[0]} ...` "
            "after --, or use --shell 'KEY=value command ...'."
        )
    if kind not in VALID_EVIDENCE_KINDS:
        valid = ", ".join(VALID_EVIDENCE_KINDS)
        raise LocalWorkflowError(f"invalid evidence kind '{kind}'. Valid: {valid}")
    if timeout_seconds < 0:
        raise LocalWorkflowError("capture timeout must be >= 0 seconds")
    if max_log_bytes < 0:
        raise LocalWorkflowError("capture max log bytes must be >= 0")
    state = ensure_state(target, no_local_files=no_local_files)
    clean_check_name = check_name.strip()
    if clean_check_name:
        try:
            ProfileContext.resolve(state.target_scope).validate_check_name(
                clean_check_name
            )
        except (KeyError, ProfileError) as e:
            raise LocalWorkflowError(str(e)) from e
    work_dir = active_work_dir(state)
    if work_dir is None:
        created = create_work(target, "implicit-work", no_local_files=no_local_files)
        work_dir = Path(created.work_dir)
    evidence_id = "ev_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    transcript = transcript_path(work_dir, evidence_id)
    started = utc_now()
    dirty_before = git_dirty(state.target_root)
    if shell_command:
        popen_args: str | list[str] = shell_command
        use_shell = True
        argv: list[str] = []
    else:
        popen_args = list(command)
        use_shell = False
        argv = list(command)

    process_result = run_process_to_transcript(
        popen_args,
        cwd=state.target_scope,
        use_shell=use_shell,
        transcript=transcript,
        no_log=no_log,
        raw_log=raw_log,
        stream_to_stderr=stream_to_stderr,
        timeout_seconds=timeout_seconds,
        max_log_bytes=max_log_bytes,
    )
    exit_code = process_result.exit_code
    ended = utc_now()
    duration_ms = process_result.duration_ms
    dirty_after = git_dirty(state.target_root)
    status = "pass" if exit_code == 0 else "fail"
    redacted_argv = redact_argv(argv, raw_log=raw_log)
    redacted_shell_command = redact_text(shell_command, raw_log=raw_log)
    redacted_display = (
        redacted_shell_command
        if shell_command
        else command_display(tuple(redacted_argv), "")
    )
    covered_paths = tuple(
        changed_paths_for_work(
            state.target_root,
            work_dir,
            exclude_paths=active_handoff_export_excludes(work_dir),
        )
    )
    record = EvidenceRecord(
        schema_version=STATE_SCHEMA_VERSION,
        id=evidence_id,
        type="command",
        capture_mode="captured",
        kind=kind,
        command_display=redacted_display,
        argv=redacted_argv,
        shell_command=redacted_shell_command,
        cwd=str(state.target_scope),
        target=str(state.target_scope),
        branch=git_branch(state.target_root),
        git_sha=git_sha(state.target_root),
        dirty_before=dirty_before,
        dirty_after=dirty_after,
        exit_code=exit_code,
        status=status,
        started_at=started,
        ended_at=ended,
        duration_ms=duration_ms,
        transcript_path=str(transcript if not no_log else ""),
        redaction="raw" if raw_log else "builtin",
        why=why,
        check_name=clean_check_name,
        diff_hash=validation_diff_hash(
            state.target_root,
            base_sha=work_start_git_sha(read_events(work_dir)),
            extra_excludes=active_handoff_export_excludes(work_dir),
        ),
        changed_paths=list(covered_paths),
        changed_path_hashes=changed_path_hashes(state.target_root, covered_paths),
        timed_out=process_result.timed_out,
        truncated=process_result.truncated,
        transcript_bytes=process_result.transcript_bytes,
    )
    with (work_dir / "evidence.jsonl").open("a") as file:
        file.write(json.dumps(asdict(record), sort_keys=True) + "\n")
    append_event(
        work_dir,
        "command_captured",
        {
            "evidence_id": evidence_id,
            "exit_code": exit_code,
            "status": status,
            "why": why,
            "check_name": clean_check_name,
        },
    )
    return CaptureResult(
        work_id=work_dir.name,
        evidence_id=evidence_id,
        exit_code=exit_code,
        status=status,
        transcript_path=str(transcript if not no_log else ""),
        why=why,
        check_name=clean_check_name,
        timed_out=process_result.timed_out,
        truncated=process_result.truncated,
        transcript_bytes=process_result.transcript_bytes,
    )


def file_sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as file_obj:
        for chunk in iter(lambda: file_obj.read(1024 * 1024), b""):
            hasher.update(chunk)
    return "sha256:" + hasher.hexdigest()


def validate_artifact_kind(kind: str) -> str:
    normalized = kind.strip()
    if not re.fullmatch(r"[a-z0-9]+(?:[-_.][a-z0-9]+)*", normalized):
        raise LocalWorkflowError(
            "invalid artifact kind: use lowercase letters, digits, hyphens, underscores, or dots"
        )
    return normalized


def artifact_filename(source: Path, *, kind: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    stem = re.sub(r"[^a-zA-Z0-9_.-]+", "-", source.name).strip(".-")
    name = stem or "artifact"
    return f"artifact_{timestamp}_{kind}_{name}"


def _artifact_record_from_event(event: EventRecord) -> ArtifactRecord | None:
    if event.type != "artifact_attached":
        return None
    data = event.data
    return ArtifactRecord(
        seq=event.seq,
        kind=str(data.get("kind", "")),
        label=str(data.get("label", "")),
        source_path=str(data.get("source_path", "")),
        artifact_path=str(data.get("artifact_path", "")),
        sha256=str(data.get("sha256", "")),
        size_bytes=int_from_event_data(data, "size_bytes"),
        copied=bool(data.get("copied", False)),
        redaction=str(data.get("redaction", "unknown")),
    )


def artifact_records(
    target: Path, *, no_local_files: bool = False
) -> ArtifactListResult:
    state = resolve_local_state(target, no_local_files=no_local_files)
    work_dir = active_work_dir(state) if state.state_dir.exists() else None
    if work_dir is None:
        return ArtifactListResult(work_id="", artifacts=[])
    records = [
        artifact
        for event in read_events(work_dir)
        if (artifact := _artifact_record_from_event(event)) is not None
    ]
    return ArtifactListResult(work_id=work_dir.name, artifacts=records)


def attach_artifact(
    target: Path,
    *,
    source_path: Path,
    kind: str,
    label: str = "",
    redaction: str = "unknown",
    copy: bool = True,
    no_local_files: bool = False,
) -> ArtifactResult:
    clean_kind = validate_artifact_kind(kind)
    if redaction not in {"none", "unknown", "external"}:
        raise LocalWorkflowError(
            "artifact redaction must be one of: none, unknown, external"
        )
    state = ensure_state(target, no_local_files=no_local_files)
    work_dir = require_work(state)
    source = source_path.expanduser().resolve()
    if not source.exists():
        raise LocalWorkflowError(f"artifact path does not exist: {source_path}")
    if not source.is_file():
        raise LocalWorkflowError(f"artifact path is not a file: {source_path}")
    size_bytes = source.stat().st_size
    digest = file_sha256(source)
    artifacts_dir = work_dir / "artifacts"
    if artifacts_dir.is_symlink():
        raise LocalWorkflowError(
            f"artifact directory must not be a symlink: {artifacts_dir}"
        )
    artifacts_dir.mkdir(exist_ok=True)
    if copy:
        destination = artifacts_dir / artifact_filename(source, kind=clean_kind)
        shutil.copy2(source, destination)
        artifact_path = str(destination)
    else:
        artifact_path = ""
    data = {
        "kind": clean_kind,
        "label": label.strip(),
        "source_path": str(source),
        "artifact_path": artifact_path,
        "sha256": digest,
        "size_bytes": size_bytes,
        "copied": copy,
        "redaction": redaction,
    }
    record = append_event(work_dir, "artifact_attached", data)
    return ArtifactResult(
        work_id=work_dir.name,
        seq=record.seq,
        kind=clean_kind,
        label=label.strip(),
        source_path=str(source),
        artifact_path=artifact_path,
        sha256=digest,
        size_bytes=size_bytes,
        copied=copy,
        redaction=redaction,
    )


def repo_surfaces(root: Path) -> list[str]:
    candidates = [
        "AGENTS.md",
        "SPEC.md",
        ".mise.toml",
        "scripts/check",
        "pyproject.toml",
        "Cargo.toml",
        "package.json",
        "go.mod",
        ".github/workflows/ci.yml",
        ".pre-commit-config.yaml",
    ]
    return [name for name in candidates if (root / name).exists()]


def find_specs(state: LocalState) -> list[str]:
    return find_specs_for_state(state)


def _sync_hash_matches(
    state: LocalState,
    work_dir: Path | None,
    recorded_hash: str,
    checkpoint_excludes: tuple[str, ...] = (),
    *,
    implicit_recorded: bool = False,
) -> bool:
    current_hash = git_diff_hash(
        state.target_root, work_freshness_excludes(work_dir, checkpoint_excludes)
    )
    if recorded_hash == current_hash:
        return True
    if implicit_recorded:
        return False
    legacy_hash = git_diff_hash(state.target_root, checkpoint_excludes)
    return recorded_hash == legacy_hash


def fresh_sync_skip(
    events: list[EventRecord], state: LocalState
) -> dict[str, object] | None:
    """Return the latest dangerous sync skip if it still covers this snapshot."""
    skips = dangerous_skip_events(events, "sync")
    if not skips:
        return None
    latest = skips[-1]
    skipped_seq = int_from_event_data(latest, "event_seq")
    skipped_hash = str(latest.get("diff_hash", ""))
    if skipped_seq < latest_sync_relevant_seq(events):
        return None
    work_dir = active_work_dir(state)
    if not _sync_hash_matches(
        state,
        work_dir,
        skipped_hash,
        implicit_recorded="implicit_excluded_paths" in latest,
    ):
        return None
    return latest


def sync_status_for(state: LocalState) -> str:
    work_dir = active_work_dir(state)
    if work_dir is None:
        return "no-active-work"
    events = read_events(work_dir)
    if not events:
        return "needs-sync"
    sync_events = [event for event in events if event.type == "sync_checkpoint"]
    if sync_events:
        latest_sync = sync_events[-1]
        synced_seq = int_from_event_data(latest_sync.data, "event_seq")
        checkpoint_excludes = normalize_exclude_paths(
            string_list_from_event_data(latest_sync.data, "excluded_paths")
        )
        if any(
            sync_exclude_safety_error(state.target_root, candidate)
            for candidate in checkpoint_excludes
        ):
            return "needs-sync"
        if checkpoint_excludes and excluded_path_state_changed(
            state.target_root,
            latest_sync.data.get("excluded"),
            expected_paths=checkpoint_excludes,
        ):
            return "needs-sync"
        if synced_seq >= latest_sync_relevant_seq(events) and _sync_hash_matches(
            state,
            work_dir,
            str(latest_sync.data.get("diff_hash", "")),
            checkpoint_excludes,
            implicit_recorded="implicit_excluded_paths" in latest_sync.data,
        ):
            return "synced"
    if sync_events and fresh_sync_skip(events, state) is not None:
        return "sync-dangerously-skipped"
    return "needs-sync"


def unique_paths(paths: list[Path]) -> list[str]:
    seen: set[str] = set()
    rows: list[str] = []
    for path in paths:
        text = str(path)
        if text in seen or not path.exists():
            continue
        seen.add(text)
        rows.append(text)
    return rows


def git_info(target: Path) -> GitInfo:
    info = DEFAULT_GIT_CLIENT.worktree_info(target)
    if info is None:
        return GitInfo(available=False)
    is_linked = (
        info.git_dir != info.git_common_dir
        and info.git_dir.parent.name == "worktrees"
        and info.git_dir.parent.parent == info.git_common_dir
    )
    return GitInfo(
        available=True,
        worktree_root=str(info.repo_root),
        git_dir=str(info.git_dir),
        git_common_dir=str(info.git_common_dir),
        is_linked_worktree=is_linked,
    )


def _state_mode_arg(state: LocalState) -> str:
    return " --no-local-files" if state.mode == "external" else ""


def _handoff_export_commands(
    state: LocalState, destination: Path | None = None
) -> dict[str, str]:
    target_arg = shlex.quote(str(state.target_scope))
    mode_arg = _state_mode_arg(state)
    output_arg = ""
    if destination is not None:
        output_arg = f" --output {shlex.quote(str(destination))}"
    return {
        "preview": f"hk handoff --target {target_arg}{mode_arg} --json",
        "generate": f"hk export --format handoff-dir{output_arg} --target {target_arg}{mode_arg}",
        "check": f"hk export --format handoff-dir{output_arg} --check --target {target_arg}{mode_arg} --json",
    }


def _start_work_commands(state: LocalState) -> dict[str, str]:
    target_arg = shlex.quote(str(state.target_scope))
    return {
        "start": "hk start demo-work --plan 'Describe the intended change' "
        f"--target {target_arg}{_state_mode_arg(state)}"
    }


def _handoff_export_status_result(
    state: LocalState,
    work_dir: Path | None,
    destination: Path | None,
    *,
    export_state: str,
    message: str,
    stale_reasons: list[str] | None = None,
) -> HandoffExportStatus:
    if work_dir is None or destination is None:
        return HandoffExportStatus(
            work_id=None,
            format="handoff-dir",
            state=export_state,
            exists=False,
            fresh=False,
            message=message,
            stale_reasons=stale_reasons or [],
            commands=_start_work_commands(state),
        )
    readme_path = destination / "README.md"
    meta_path = destination / "meta.json"
    return HandoffExportStatus(
        work_id=work_dir.name,
        format="handoff-dir",
        state=export_state,
        exists=destination.exists(),
        fresh=export_state == "fresh",
        path=str(destination),
        relative_path=_relative_to_root(destination, state.target_root),
        readme_path=str(readme_path),
        meta_path=str(meta_path),
        readme_exists=readme_path.exists(),
        message=message,
        stale_reasons=stale_reasons or [],
        commands=_handoff_export_commands(state, destination),
    )


def _expected_export_files(
    state: LocalState,
    work_dir: Path,
    *,
    output_relative: str,
    events: list[EventRecord],
) -> dict[str, str]:
    handoff_content = _sanitize_export_content(
        _sanitize_export_artifact_paths(
            render_handoff(
                work_dir,
                state,
                format="markdown",
                freshness_excludes=(output_relative,),
            ),
            events,
        ),
        state,
    )
    return {
        "README.md": _export_readme(
            work_dir.name,
            handoff_content,
            output_relative,
            state,
        ),
        "artifacts/README.md": _artifacts_readme(),
    }


def _normalized_expected_export_content(relative: str, content: str) -> str:
    return content


def _status_from_export_check_details(
    state: LocalState,
    work_dir: Path,
    destination: Path,
    metadata: dict[str, object],
    artifact_files: list[tuple[Path, str, str]],
    expected_file_hashes: dict[str, str] | None = None,
    expected_file_contents: dict[str, str] | None = None,
) -> HandoffExportStatus:
    meta_path = destination / "meta.json"
    if not meta_path.exists():
        return _handoff_export_status_result(
            state,
            work_dir,
            destination,
            export_state="missing",
            message=f"HK export metadata missing: {meta_path}",
            stale_reasons=["metadata missing"],
        )
    if meta_path.is_symlink():
        return _handoff_export_status_result(
            state,
            work_dir,
            destination,
            export_state="invalid",
            message=f"HK export metadata must not be a symlink: {meta_path}",
            stale_reasons=["metadata symlink"],
        )
    try:
        recorded = json.loads(meta_path.read_text())
    except json.JSONDecodeError as e:
        return _handoff_export_status_result(
            state,
            work_dir,
            destination,
            export_state="invalid",
            message=f"invalid HK export metadata {meta_path}: {e}",
            stale_reasons=["invalid metadata json"],
        )
    if not isinstance(recorded, dict):
        return _handoff_export_status_result(
            state,
            work_dir,
            destination,
            export_state="invalid",
            message=f"invalid HK export metadata {meta_path}: expected JSON object",
            stale_reasons=["invalid metadata object"],
        )
    expected_files = metadata.get("files", [])
    if not isinstance(expected_files, list):
        return _handoff_export_status_result(
            state,
            work_dir,
            destination,
            export_state="invalid",
            message=f"HK export metadata files field is invalid: {meta_path}",
            stale_reasons=["invalid files field"],
        )
    missing_files = [
        str(item) for item in expected_files if not (destination / str(item)).exists()
    ]
    recorded_hashes = recorded.get("file_hashes", {})
    if not isinstance(recorded_hashes, dict):
        return _handoff_export_status_result(
            state,
            work_dir,
            destination,
            export_state="invalid",
            message=f"HK export metadata file_hashes field is invalid: {meta_path}",
            stale_reasons=["invalid file_hashes field"],
        )
    expected_artifact_hashes = {
        relative: digest for _, relative, digest in artifact_files
    }
    expected_generated_hashes = expected_file_hashes or {}
    expected_hashes = {
        **expected_generated_hashes,
        **expected_artifact_hashes,
    }
    stale_generated_hashes = [
        relative
        for relative, digest in expected_generated_hashes.items()
        if recorded_hashes.get(relative) != digest
    ]
    for relative in expected_file_contents or {}:
        if relative not in recorded_hashes and relative not in stale_generated_hashes:
            stale_generated_hashes.append(relative)
    stale_artifact_hashes = [
        relative
        for relative, digest in expected_artifact_hashes.items()
        if recorded_hashes.get(relative) != digest
    ]
    unsafe_hash_paths: list[str] = []
    unexpected_hash_paths: list[str] = []
    hash_mismatches: list[str] = []
    artifact_hash_mismatches: list[str] = []
    symlink_files = [
        str(item) for item in expected_files if (destination / str(item)).is_symlink()
    ]
    expected_file_set = {str(item) for item in expected_files}
    unexpected_files: list[str] = []
    for path in destination.rglob("*") if destination.exists() else []:
        if path.is_dir() and not path.is_symlink():
            continue
        relative = path.relative_to(destination).as_posix()
        if relative not in expected_file_set:
            unexpected_files.append(relative)
    for relative, expected_hash in recorded_hashes.items():
        safe_relative = _safe_export_relative(str(relative))
        if safe_relative is None:
            unsafe_hash_paths.append(str(relative))
            continue
        if safe_relative not in expected_file_set:
            unexpected_hash_paths.append(safe_relative)
            continue
        hashed_path = destination / safe_relative
        if hashed_path.is_symlink():
            if safe_relative not in symlink_files:
                symlink_files.append(safe_relative)
            continue
        if not hashed_path.exists():
            continue
        actual_hash = _file_hash(hashed_path)
        if expected_file_contents and safe_relative in expected_file_contents:
            if recorded_hashes.get(safe_relative) != actual_hash:
                if safe_relative not in stale_generated_hashes:
                    stale_generated_hashes.append(safe_relative)
            expected_content = _normalized_expected_export_content(
                safe_relative, expected_file_contents[safe_relative]
            )
            try:
                actual_text = hashed_path.read_text()
            except UnicodeDecodeError:
                hash_mismatches.append(safe_relative)
                continue
            actual_content = _normalized_expected_export_content(
                safe_relative, actual_text
            )
            if actual_content != expected_content:
                hash_mismatches.append(safe_relative)
            continue
        if safe_relative in expected_artifact_hashes:
            if actual_hash != expected_artifact_hashes[safe_relative]:
                artifact_hash_mismatches.append(safe_relative)
        elif safe_relative in expected_hashes:
            if actual_hash != expected_hashes[safe_relative]:
                hash_mismatches.append(safe_relative)
        elif actual_hash != expected_hash:
            hash_mismatches.append(safe_relative)
    mismatches = _compare_export_metadata(metadata, recorded)
    if not (
        missing_files
        or mismatches
        or hash_mismatches
        or unsafe_hash_paths
        or unexpected_hash_paths
        or unexpected_files
        or artifact_hash_mismatches
        or stale_generated_hashes
        or stale_artifact_hashes
        or symlink_files
    ):
        return _handoff_export_status_result(
            state,
            work_dir,
            destination,
            export_state="fresh",
            message="HK export is fresh",
        )
    details = []
    invalid_details = []
    if missing_files:
        details.append("missing files: " + ", ".join(missing_files))
    if mismatches:
        details.append("stale metadata: " + ", ".join(mismatches))
    if hash_mismatches:
        details.append("modified generated files: " + ", ".join(hash_mismatches))
    if artifact_hash_mismatches:
        details.append(
            "modified attached artifacts: " + ", ".join(artifact_hash_mismatches)
        )
    if unsafe_hash_paths:
        invalid_details.append(
            "unsafe file_hashes paths: " + ", ".join(unsafe_hash_paths)
        )
    if unexpected_hash_paths:
        invalid_details.append(
            "unexpected file_hashes paths: " + ", ".join(unexpected_hash_paths)
        )
    if unexpected_files:
        invalid_details.append("unexpected files: " + ", ".join(unexpected_files))
    if stale_generated_hashes:
        details.append(
            "stale generated file hashes: " + ", ".join(stale_generated_hashes)
        )
    if stale_artifact_hashes:
        details.append(
            "stale attached artifact hashes: " + ", ".join(stale_artifact_hashes)
        )
    if symlink_files:
        invalid_details.append("symlinked files: " + ", ".join(symlink_files))
    all_details = details + invalid_details
    return _handoff_export_status_result(
        state,
        work_dir,
        destination,
        export_state="invalid" if invalid_details else "stale",
        message="HK export is stale or incomplete: " + "; ".join(all_details),
        stale_reasons=all_details,
    )


def _handoff_export_status_for_state(
    state: LocalState,
    work_dir: Path | None,
    *,
    output_path: Path | None = None,
    exact: bool = True,
) -> HandoffExportStatus:
    if work_dir is None:
        return _handoff_export_status_result(
            state,
            None,
            None,
            export_state="no-active-work",
            message="No active HK work",
            stale_reasons=["no active work"],
        )
    destination = output_path or (state.target_root / ".ai" / "hk" / work_dir.name)
    if not destination.is_absolute():
        destination = state.target_root / destination
    try:
        reject_symlink_ancestors(destination)
    except HandoffExportError as e:
        return _handoff_export_status_result(
            state,
            work_dir,
            destination,
            export_state="invalid",
            message=str(e),
            stale_reasons=["unsafe export path"],
        )
    if not exact:
        meta_path = destination / "meta.json"
        readme_path = destination / "README.md"
        if not meta_path.exists():
            return _handoff_export_status_result(
                state,
                work_dir,
                destination,
                export_state="missing",
                message=f"HK export metadata missing: {meta_path}",
                stale_reasons=["metadata missing"],
            )
        if meta_path.is_symlink():
            return _handoff_export_status_result(
                state,
                work_dir,
                destination,
                export_state="invalid",
                message=f"HK export metadata must not be a symlink: {meta_path}",
                stale_reasons=["metadata symlink"],
            )
        if not readme_path.exists():
            return _handoff_export_status_result(
                state,
                work_dir,
                destination,
                export_state="missing",
                message=f"HK export README missing: {readme_path}",
                stale_reasons=["README missing"],
            )
    output_relative = _relative_to_root(destination, state.target_root)
    events = read_events(work_dir)
    evidence = read_evidence(work_dir)
    readiness = ready_for_work(
        work_dir,
        state,
        check_handoff=False,
        freshness_excludes=(output_relative,),
    )
    try:
        artifact_files = _copied_artifacts_for_export(work_dir, events)
        expected_files = _expected_export_files(
            state,
            work_dir,
            output_relative=output_relative,
            events=events,
        )
        expected_file_hashes = {
            relative: _text_hash(content)
            for relative, content in expected_files.items()
            if relative != "README.md"
        }
        metadata = _handoff_dir_metadata(
            state=state,
            work_dir=work_dir,
            output_path=destination,
            events=events,
            evidence=evidence,
            readiness=readiness,
        )
    except LocalWorkflowError as e:
        return _handoff_export_status_result(
            state,
            work_dir,
            destination,
            export_state="invalid",
            message=str(e),
            stale_reasons=[str(e)],
        )
    return _status_from_export_check_details(
        state,
        work_dir,
        destination,
        metadata,
        artifact_files,
        expected_file_hashes,
        expected_files,
    )


def handoff_export_status(
    target: Path,
    *,
    output_path: Path | None = None,
    no_local_files: bool = False,
) -> HandoffExportStatus:
    state = resolve_local_state(target, no_local_files=no_local_files)
    work_dir = active_work_dir(state) if state.state_dir.exists() else None
    return _handoff_export_status_for_state(
        state,
        work_dir,
        output_path=output_path,
    )


def brief(target: Path, *, no_local_files: bool = False) -> Brief:
    state = resolve_local_state(target, no_local_files=no_local_files)
    active = active_work_dir(state) if state.state_dir.exists() else None
    try:
        profile_catalog, harness_config = load_profile_catalog()
        profiles = list(profile_names(profile_catalog))
    except ProfileError as e:
        raise LocalWorkflowError(str(e)) from e
    try:
        profile_resolution = resolve_profile(
            state.target_scope, catalog=profile_catalog, config=harness_config
        )
        configured_system_map = profile_resolution.system_map
    except KeyError:
        # `hk brief` should stay a resilient repo-shape probe. A misconfigured
        # target profile can make `hk checks` fail, but it should not prevent a
        # user or agent from reading the basic repo brief or target-level map.
        configured_system_map = resolve_target_system_map(
            state.target_scope, config=harness_config
        )
    spec_sources = (
        find_specs(state)
        if state.state_dir.exists()
        else unique_paths(
            [state.target_scope / "SPEC.md", state.target_root / "SPEC.md"]
        )
    )
    system_map_result = load_system_map(
        state.target_root, configured_path=configured_system_map
    )
    system_map_summary = (
        summary_from_load_result(system_map_result, repo_root=state.target_root)
        if system_map_result is not None
        else None
    )
    return Brief(
        target_root=str(state.target_root),
        target_scope=str(state.target_scope),
        branch=git_branch(state.target_root),
        git_sha=git_sha(state.target_root),
        dirty=git_dirty(state.target_root),
        state_dir=str(state.state_dir),
        state_exists=state.state_dir.exists(),
        active_work=active.name if active else "",
        sync_status=sync_status_for(state) if active else "no-active-work",
        agents_md=unique_paths(
            [state.target_scope / "AGENTS.md", state.target_root / "AGENTS.md"]
        ),
        spec_sources=spec_sources,
        repo_surfaces=repo_surfaces(state.target_root),
        profiles=profiles,
        system_map=system_map_summary,
        git=git_info(state.target_scope),
        handoff_export=_handoff_export_status_for_state(state, active, exact=False),
    )


def brief_markdown(value: Brief) -> str:
    lines = [
        "# Current Repo Brief",
        "",
        "## Repo state",
        f"- Target root: `{value.target_root}`",
        f"- Target scope: `{value.target_scope}`",
        f"- Branch: `{value.branch}`",
        f"- Git SHA: `{value.git_sha}`",
        f"- Dirty: `{str(value.dirty).lower()}`",
        "",
        "## Git worktree",
        f"- Git available: `{str(value.git.available).lower()}`",
        f"- Worktree root: `{value.git.worktree_root or 'unknown'}`",
        f"- Git dir: `{value.git.git_dir or 'unknown'}`",
        f"- Git common dir: `{value.git.git_common_dir or 'unknown'}`",
        f"- Linked worktree: `{str(value.git.is_linked_worktree).lower()}`",
        "",
        "## Harness state",
        f"- State exists: `{str(value.state_exists).lower()}`",
        f"- State dir: `{value.state_dir}`",
        f"- Active work: `{value.active_work or 'none'}`",
        f"- Sync status: `{value.sync_status}`",
        "",
        "## Handoff export",
        f"- State: `{value.handoff_export.state}`",
        f"- Fresh: `{str(value.handoff_export.fresh).lower()}`",
        f"- Path: `{value.handoff_export.path or 'none'}`",
        f"- README: `{value.handoff_export.readme_path or 'none'}`",
        f"- Message: {value.handoff_export.message}",
        "",
        "## Instructions and specs",
    ]
    lines.extend(
        [f"- AGENTS: `{path}`" for path in value.agents_md] or ["- AGENTS: none found"]
    )
    lines.extend(
        [f"- SPEC: `{path}`" for path in value.spec_sources] or ["- SPEC: none found"]
    )
    lines.extend(["", "## Repo surfaces"])
    lines.extend(
        [f"- `{surface}`" for surface in value.repo_surfaces] or ["- none detected"]
    )
    lines.extend(
        [
            "",
            "## Profiles",
            "Use `hk profile list --target <target> --json` and repo instructions to choose a profile. No profile is auto-selected here.",
        ]
    )
    lines.extend([f"- `{profile}`" for profile in value.profiles])
    lines.extend(["", "## System map"])
    if value.system_map is None:
        lines.append("- none found")
    else:
        lines.append(
            f"- `{value.system_map.path}` ({value.system_map.source}): "
            f"{value.system_map.status}, {value.system_map.components} components, "
            f"{value.system_map.invariants} invariants, {value.system_map.errors_count} errors, "
            f"{value.system_map.warnings_count} warnings"
        )
        if value.system_map.overrides:
            lines.append(f"  - overrides `{value.system_map.overrides}`")
    return "\n".join(lines) + "\n"


def render_handoff(
    work_dir: Path,
    state: LocalState,
    *,
    format: HandoffFormat = "markdown",
    freshness_excludes: tuple[str, ...] = (),
) -> str:
    events = read_events(work_dir)
    evidence = read_evidence(work_dir)
    render = render_handoff_pr_markdown if format == "pr" else render_handoff_markdown
    return render(
        work_id=work_dir.name,
        branch=git_branch(state.target_root),
        git_sha=git_sha(state.target_root),
        dirty=git_dirty(state.target_root),
        sync_status=sync_status_for(state),
        events=events,
        evidence=evidence,
        readiness=ready_for_work(
            work_dir,
            state,
            check_handoff=False,
            freshness_excludes=freshness_excludes,
        ),
    )


def _status_changed_paths(root: Path) -> list[str]:
    return git_snapshot.status_changed_paths(root)


def _diff_changed_paths(root: Path, base_sha: str) -> list[str]:
    return git_snapshot.diff_changed_paths(root, base_sha)


def _untracked_paths(root: Path) -> list[str]:
    return git_snapshot.untracked_paths(root)


def work_start_git_sha(events: list[EventRecord]) -> str:
    for event in events:
        if event.type == "work_started":
            return str(event.data.get("git_sha") or "")
    return ""


def changed_paths(root: Path, *, base_sha: str = "") -> list[str]:
    paths = [
        *_diff_changed_paths(root, base_sha),
        *_status_changed_paths(root),
        *_untracked_paths(root),
    ]
    return list(dict.fromkeys(path.replace("\\", "/") for path in paths if path))


def changed_paths_for_work(
    root: Path, work_dir: Path, *, exclude_paths: tuple[str, ...] = ()
) -> list[str]:
    paths = changed_paths(root, base_sha=work_start_git_sha(read_events(work_dir)))
    return list(
        _filtered_changed_paths(
            tuple(paths), work_freshness_excludes(work_dir, exclude_paths)
        )
    )


def review_prompt(
    target: Path, *, review_name: str = "", no_local_files: bool = False
) -> ReviewPromptResult:
    state = ensure_state(target, no_local_files=no_local_files)
    work_dir = require_work(state)
    profile_review = None
    if review_name.strip():
        try:
            profile_review = ProfileContext.resolve(state.target_scope).review_named(
                review_name.strip()
            )
        except (KeyError, ProfileError) as e:
            raise LocalWorkflowError(str(e)) from e
    prompt = render_review_prompt(
        work_id=work_dir.name,
        target_root=str(state.target_root),
        branch=git_branch(state.target_root),
        events=read_events(work_dir),
        evidence=read_evidence(work_dir),
        changed_paths=changed_paths_for_work(state.target_root, work_dir),
        profile_review=profile_review,
    )
    return ReviewPromptResult(work_id=work_dir.name, prompt=prompt)


def add_review(
    target: Path,
    *,
    backend: str,
    reviewer: str,
    summary: str,
    disposition: str = "accepted",
    review_name: str = "",
    reviewed_paths: tuple[str, ...] = (),
    no_local_files: bool = False,
) -> ReviewResult:
    if not backend.strip():
        raise LocalWorkflowError("review requires --backend")
    if not reviewer.strip():
        raise LocalWorkflowError("review requires --reviewer")
    if is_self_review_identity(backend) or is_self_review_identity(reviewer):
        raise LocalWorkflowError(f"review must be independent: {SELF_REVIEW_GUIDANCE}")
    if not summary.strip():
        raise LocalWorkflowError("review requires --summary")
    state = ensure_state(target, no_local_files=no_local_files)
    work_dir = require_work(state)
    clean_review_name = review_name.strip()
    if clean_review_name:
        try:
            ProfileContext.resolve(state.target_scope).review_named(clean_review_name)
        except (KeyError, ProfileError) as e:
            raise LocalWorkflowError(str(e)) from e
    current_changed_paths = tuple(changed_paths_for_work(state.target_root, work_dir))
    normalized_reviewed_paths: list[str] = []
    for path in reviewed_paths:
        clean_path = path.strip().replace("\\", "/")
        while clean_path.startswith("./"):
            clean_path = clean_path[2:]
        clean_path = clean_path.strip("/")
        if clean_path:
            normalized_reviewed_paths.append(clean_path)
    clean_reviewed_paths = tuple(dict.fromkeys(normalized_reviewed_paths))
    if clean_reviewed_paths:
        current_changed_set = set(current_changed_paths)
        unknown_paths = [
            path for path in clean_reviewed_paths if path not in current_changed_set
        ]
        if unknown_paths:
            preview = ", ".join(unknown_paths[:3])
            raise LocalWorkflowError(
                "review --path must name currently changed repo-relative paths; "
                f"not currently changed: {preview}"
            )
    covered_paths = clean_reviewed_paths or current_changed_paths
    record_data: dict[str, object] = {
        "backend": backend.strip(),
        "reviewer": reviewer.strip(),
        "summary": summary.strip(),
        "disposition": disposition.strip() or "accepted",
        "diff_hash": validation_diff_hash(
            state.target_root,
            base_sha=work_start_git_sha(read_events(work_dir)),
            extra_excludes=active_handoff_export_excludes(work_dir),
        ),
        "changed_paths": list(covered_paths),
        "changed_path_hashes": changed_path_hashes(state.target_root, covered_paths),
    }
    if clean_review_name:
        record_data["review_name"] = clean_review_name
    record = append_event(work_dir, "review_added", record_data)
    return ReviewResult(
        work_id=work_dir.name,
        seq=record.seq,
        backend=backend.strip(),
        reviewer=reviewer.strip(),
        summary=summary.strip(),
        disposition=disposition.strip() or "accepted",
        review_name=clean_review_name,
        reviewed_paths=list(covered_paths),
    )


def add_dangerous_skip(
    target: Path,
    *,
    check: str,
    label: str,
    reason: str,
    mitigation: str,
    no_local_files: bool = False,
) -> DangerousSkipResult:
    if check not in {"review", "validation", "sync"}:
        raise LocalWorkflowError("dangerously-skip supports: review, validation, sync")
    if not label.strip():
        raise LocalWorkflowError("dangerously-skip requires --label")
    if not reason.strip():
        raise LocalWorkflowError("dangerously-skip requires --reason")
    if not mitigation.strip():
        raise LocalWorkflowError("dangerously-skip requires --mitigation")
    state = ensure_state(target, no_local_files=no_local_files)
    work_dir = require_work(state)
    data: dict[str, object] = {
        "check": check,
        "label": label.strip(),
        "reason": reason.strip(),
        "mitigation": mitigation.strip(),
    }
    if check == "sync":
        events = read_events(work_dir)
        if not any(event.type == "sync_checkpoint" for event in events):
            raise LocalWorkflowError(
                "dangerously-skip sync requires a prior `hk sync` checkpoint"
            )
        implicit_excludes = active_handoff_export_excludes(work_dir)
        data.update(
            {
                "git_sha": git_sha(state.target_root),
                "diff_hash": git_diff_hash(state.target_root, implicit_excludes),
                "event_seq": max((event.seq for event in events), default=0) + 1,
            }
        )
        if implicit_excludes:
            data["implicit_excluded_paths"] = list(implicit_excludes)
    elif check in {"validation", "review"}:
        data.update(
            {
                "git_sha": git_sha(state.target_root),
                "diff_hash": validation_diff_hash(
                    state.target_root,
                    base_sha=work_start_git_sha(read_events(work_dir)),
                    extra_excludes=active_handoff_export_excludes(work_dir),
                ),
            }
        )
    record = append_event(work_dir, "dangerous_skip_added", data)
    return DangerousSkipResult(
        work_id=work_dir.name,
        seq=record.seq,
        check=check,
        label=label.strip(),
        reason=reason.strip(),
        mitigation=mitigation.strip(),
    )


def ready(target: Path, *, no_local_files: bool = False) -> ReadyResult:
    state = ensure_state(target, no_local_files=no_local_files)
    work_dir = require_work(state)
    return ready_for_work(work_dir, state, check_handoff=True)


def required_profile_items_for_work(
    state: LocalState, work_dir: Path, *, changed_paths: tuple[str, ...] | None = None
) -> tuple[tuple[RequiredProfileItem, ...], tuple[RequiredProfileItem, ...]]:
    try:
        context = ProfileContext.resolve(
            state.target_scope,
            repo_root=state.target_root,
            changed_paths=changed_paths
            if changed_paths is not None
            else tuple(changed_paths_for_work(state.target_root, work_dir)),
        )
    except (KeyError, ProfileError) as e:
        raise LocalWorkflowError(str(e)) from e
    assert context.view is not None
    view = context.view
    required_checks = tuple(
        RequiredProfileItem(
            name=item.name,
            purpose=item.purpose,
            matched_paths=item.matched_paths,
        )
        for item in view.suggested_checks
        if item.required
    )
    required_reviews = tuple(
        RequiredProfileItem(
            name=item.name,
            purpose=item.purpose,
            matched_paths=item.matched_paths,
        )
        for item in view.suggested_reviews
        if item.required
    )
    return required_checks, required_reviews


def _path_is_under_any(path: str, prefixes: tuple[str, ...]) -> bool:
    return any(
        path == prefix or path.startswith(f"{prefix.rstrip('/')}/")
        for prefix in prefixes
    )


def _filtered_changed_paths(
    paths: tuple[str, ...], excludes: tuple[str, ...]
) -> tuple[str, ...]:
    return tuple(path for path in paths if not _path_is_under_any(path, excludes))


def ready_for_work(
    work_dir: Path,
    state: LocalState,
    *,
    check_handoff: bool = True,
    freshness_excludes: tuple[str, ...] = (),
) -> ReadyResult:
    events = read_events(work_dir)
    evidence = read_evidence(work_dir)
    effective_freshness_excludes = work_freshness_excludes(work_dir, freshness_excludes)
    current_changed_paths = _filtered_changed_paths(
        tuple(changed_paths_for_work(state.target_root, work_dir)),
        effective_freshness_excludes,
    )
    required_checks, required_reviews = required_profile_items_for_work(
        state, work_dir, changed_paths=current_changed_paths
    )
    sync_status = sync_status_for(state)
    if sync_status == "sync-dangerously-skipped":
        current_diff_hashes = (
            validation_diff_hash(
                state.target_root,
                base_sha=work_start_git_sha(events),
                extra_excludes=(
                    *COMMON_AGENT_LOCAL_STATE_PATHS,
                    *effective_freshness_excludes,
                ),
            ),
            validation_diff_hash(
                state.target_root,
                base_sha=work_start_git_sha(events),
                extra_excludes=effective_freshness_excludes,
            ),
        )
        review_excludes = COMMON_AGENT_LOCAL_STATE_PATHS
    else:
        sync_excludes = latest_sync_excluded_paths(events)
        review_excludes = sync_excludes
        current_diff_hashes = (
            validation_diff_hash(
                state.target_root,
                base_sha=work_start_git_sha(events),
                extra_excludes=(*sync_excludes, *effective_freshness_excludes),
            ),
            validation_diff_hash(
                state.target_root,
                base_sha=work_start_git_sha(events),
                extra_excludes=effective_freshness_excludes,
            ),
        )
    review_changed_paths = tuple(
        path
        for path in current_changed_paths
        if not _path_is_under_any(path, review_excludes)
    )
    return ready_for_events(
        work_id=work_dir.name,
        events=events,
        evidence=evidence,
        sync_status=sync_status,
        agent_local_warning=agent_local_state_warning(state.target_root),
        current_diff_hashes=current_diff_hashes,
        check_handoff=check_handoff,
        handoff_check=lambda: render_handoff(work_dir, state),
        required_profile_checks=required_checks,
        required_profile_reviews=required_reviews,
        changed_paths=review_changed_paths,
        current_changed_path_hashes=changed_path_hashes(
            state.target_root,
            review_changed_paths,
        ),
    )


def lifecycle_phase(events: list[EventRecord], readiness: ReadyResult | None) -> str:
    return policy_lifecycle_phase(events, readiness)


def status(target: Path, *, no_local_files: bool = False) -> StatusResult:
    state = resolve_local_state(target, no_local_files=no_local_files)
    work_dir = active_work_dir(state) if state.state_dir.exists() else None
    if work_dir is None:
        return StatusResult(
            active_work="",
            target_root=str(state.target_root),
            target_scope=str(state.target_scope),
            state_dir=str(state.state_dir),
            sync_status="no-active-work",
            ready_status="not-started",
            phase="not-started",
            checks=[],
            next_actions=[
                "start: hk start demo-work --plan 'Describe the intended change and validation approach'"
            ],
            suggested_checks=[],
            suggested_reviews=[],
            invariant_supersessions=[],
            evidence_freshness=[],
            export_freshness=None,
        )

    events = read_events(work_dir)
    readiness = ready_for_work(work_dir, state, check_handoff=False)
    profile_view = None
    try:
        profile_view = ProfileContext.resolve(
            state.target_scope,
            repo_root=state.target_root,
            changed_paths=tuple(changed_paths_for_work(state.target_root, work_dir)),
        ).view
    except (KeyError, ProfileError):
        profile_view = None
    suggested_checks = [
        item
        for item in (profile_view.suggested_checks if profile_view else ())
        if not item.required
    ]
    suggested_reviews = [
        item
        for item in (profile_view.suggested_reviews if profile_view else ())
        if not item.required
    ]
    current_changed_paths = tuple(changed_paths_for_work(state.target_root, work_dir))
    status_sync_status = sync_status_for(state)
    if status_sync_status == "sync-dangerously-skipped":
        freshness_paths = _filtered_changed_paths(
            current_changed_paths, COMMON_AGENT_LOCAL_STATE_PATHS
        )
        current_diff_hashes = (
            validation_diff_hash(
                state.target_root,
                base_sha=work_start_git_sha(events),
                extra_excludes=(
                    *COMMON_AGENT_LOCAL_STATE_PATHS,
                    *active_handoff_export_excludes(work_dir),
                ),
            ),
            validation_diff_hash(
                state.target_root,
                base_sha=work_start_git_sha(events),
                extra_excludes=active_handoff_export_excludes(work_dir),
            ),
        )
    else:
        sync_excludes = latest_sync_excluded_paths(events)
        freshness_paths = _filtered_changed_paths(current_changed_paths, sync_excludes)
        current_diff_hashes = (
            validation_diff_hash(
                state.target_root,
                base_sha=work_start_git_sha(events),
                extra_excludes=(
                    *sync_excludes,
                    *active_handoff_export_excludes(work_dir),
                ),
            ),
            validation_diff_hash(
                state.target_root,
                base_sha=work_start_git_sha(events),
                extra_excludes=active_handoff_export_excludes(work_dir),
            ),
        )
    try:
        required_checks, required_reviews = required_profile_items_for_work(
            state, work_dir, changed_paths=freshness_paths
        )
    except LocalWorkflowError:
        required_checks, required_reviews = (), ()
    evidence_freshness = build_evidence_freshness_items(
        work_id=work_dir.name,
        events=events,
        evidence=read_evidence(work_dir),
        current_paths=freshness_paths,
        current_path_hashes=changed_path_hashes(state.target_root, freshness_paths),
        current_diff_hashes=current_diff_hashes,
        required_checks=required_checks,
        required_reviews=required_reviews,
    )
    export_freshness = build_export_freshness_note(
        work_id=work_dir.name,
        target_root=str(state.target_root),
        all_changed_paths=tuple(
            changed_paths(state.target_root, base_sha=work_start_git_sha(events))
        ),
    )
    actions: list[str] = []
    if not notes_by_kind(events, "plan"):
        actions.append(
            "plan: hk plan 'Describe the intended change and validation approach' (next time: hk start demo-work --plan '...')"
        )
    if not notes_by_kinds(events, ("context", "background")):
        actions.append(
            "context (optional): hk context 'Constraints, relevant files, or repo facts' if it prevents rediscovery"
        )
    if not notes_by_kind(events, "decision") or not notes_by_kind(
        events, "spec-impact"
    ):
        actions.append(
            "decision: hk decide 'Decision/spec reflection' --spec-impact none|updated|not-needed [--spec-ref PATH]"
        )
    check_map = {check.id: check for check in readiness.checks}
    if check_map.get("validation") and check_map["validation"].status == "fail":
        actions.append(
            "validation: hk validate --why 'Fast gate passes' -- mise run check"
        )
    if check_map.get("review") and check_map["review"].status == "fail":
        actions.append(
            "review required: do not skip just because the implementation agent cannot self-review. Run `hk review prompt`, dispatch that prompt through an independent AI/tool or fresh-context subagent if your harness supports one (Pi `subagent` tool, Claude Code `Agent` tool/`Task` alias, Codex Shell tool running `codex review --uncommitted`), record with `hk review add ...`, then re-run `hk status`; only use `hk dangerously-skip review --label no-review --reason ... --mitigation ...` when no independent review path is available"
        )
    for check in readiness.checks:
        if check.status == "fail" and check.id.startswith("profile-check:"):
            actions.append(f"validation: {check.message}")
        if check.status == "fail" and check.id.startswith("profile-review:"):
            actions.append(f"review: {check.message}")
    if check_map.get("sync") and check_map["sync"].status == "fail":
        warning = agent_local_state_warning(state.target_root)
        sync_action = (
            "sync: agent-local state is blocking readiness."
            if warning
            else "sync: hk sync after reconciling changes"
        )
        if warning:
            sync_action += warning
        actions.append(sync_action)
    invariant_supersessions = [
        item.as_payload()
        for item in lifecycle_events.invariant_supersession_events(events)
    ]
    if readiness.ready:
        actions.append("handoff: hk handoff")
    for item in lifecycle_events.invariant_supersession_events(events):
        actions.append(
            "invariant supersession: ensure commit message includes "
            f"`Supersedes-Invariant: {item.invariant}` and PR description/handoff calls out the supersession"
        )
    return StatusResult(
        active_work=work_dir.name,
        target_root=str(state.target_root),
        target_scope=str(state.target_scope),
        state_dir=str(state.state_dir),
        sync_status=sync_status_for(state),
        ready_status=readiness.status,
        phase=lifecycle_phase(events, readiness),
        checks=readiness.checks,
        next_actions=actions,
        suggested_checks=suggested_checks,
        suggested_reviews=suggested_reviews,
        invariant_supersessions=invariant_supersessions,
        evidence_freshness=evidence_freshness,
        export_freshness=export_freshness,
    )


def materialize_work(target: Path, *, no_local_files: bool = False) -> HandoffResult:
    state = ensure_state(target, no_local_files=no_local_files)
    work_dir = require_work(state)
    events = read_events(work_dir)
    views = work_dir / "views"
    write_note_views(views, events)
    handoff = render_handoff(work_dir, state)
    path = views / "handoff.md"
    path.write_text(handoff)
    return HandoffResult(work_id=work_dir.name, content=handoff, path=str(path))


def summary(target: Path, *, no_local_files: bool = False) -> HandoffResult:
    state = ensure_state(target, no_local_files=no_local_files)
    work_dir = require_work(state)
    events = read_events(work_dir)
    evidence = read_evidence(work_dir)
    content = render_summary_markdown(
        work_id=work_dir.name,
        branch=git_branch(state.target_root),
        git_sha=git_sha(state.target_root),
        dirty=git_dirty(state.target_root),
        sync_status=sync_status_for(state),
        events=events,
        evidence=evidence,
        readiness=ready_for_work(work_dir, state, check_handoff=False),
    )
    return HandoffResult(work_id=work_dir.name, content=content)


def handoff(
    target: Path,
    *,
    output_path: Path | None = None,
    no_local_files: bool = False,
    format: HandoffFormat = "markdown",
) -> HandoffResult:
    state = ensure_state(target, no_local_files=no_local_files)
    work_dir = require_work(state)
    content = render_handoff(work_dir, state, format=format)
    path_text = ""
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content)
        path_text = str(output_path)
    return HandoffResult(work_id=work_dir.name, content=content, path=path_text)


def _relative_to_root(path: Path, root: Path) -> str:
    try:
        return (
            path.resolve(strict=False)
            .relative_to(root.resolve(strict=False))
            .as_posix()
        )
    except ValueError:
        return str(path.resolve(strict=False))


def _export_relevant_events(events: list[EventRecord]) -> list[EventRecord]:
    return [event for event in events if event.type not in SYNC_IGNORED_EVENT_TYPES]


def _event_count(events: list[EventRecord]) -> int:
    return len(_export_relevant_events(events))


def _max_event_seq(events: list[EventRecord]) -> int:
    return max((event.seq for event in _export_relevant_events(events)), default=0)


def _text_hash(content: str) -> str:
    return "sha256:" + hashlib.sha256(content.encode("utf-8")).hexdigest()


def _file_hash(path: Path) -> str:
    if path.is_symlink():
        raise LocalWorkflowError(f"HK export contains symlinked file: {path}")
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _artifact_export_filename(record: ArtifactRecord) -> str:
    clean_kind = validate_artifact_kind(record.kind)
    source_name = Path(record.artifact_path or record.source_path).name or "artifact"
    clean_name = re.sub(r"[^a-zA-Z0-9_.-]+", "-", source_name).strip(".-")
    clean_name = clean_name or "artifact"
    return f"artifact_{record.seq}_{clean_kind}_{clean_name}"


def _attached_artifact_export_records(
    events: list[EventRecord],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for event in events:
        record = _artifact_record_from_event(event)
        if record is None:
            continue
        export_path = (
            f"artifacts/{_artifact_export_filename(record)}" if record.copied else ""
        )
        rows.append(
            {
                "seq": record.seq,
                "kind": record.kind,
                "label": record.label,
                "redaction": record.redaction,
                "copied": record.copied,
                "export_path": export_path,
                "sha256": record.sha256,
                "size_bytes": record.size_bytes,
            }
        )
    return rows


def _copied_artifacts_for_export(
    work_dir: Path, events: list[EventRecord]
) -> list[tuple[Path, str, str]]:
    rows: list[tuple[Path, str, str]] = []
    artifacts_dir_raw = work_dir / "artifacts"
    if artifacts_dir_raw.is_symlink():
        raise LocalWorkflowError(
            f"artifact directory must not be a symlink: {artifacts_dir_raw}"
        )
    artifacts_dir = artifacts_dir_raw.resolve(strict=False)
    for event in events:
        record = _artifact_record_from_event(event)
        if record is None or not record.copied:
            continue
        raw_source = Path(record.artifact_path)
        try:
            source = raw_source.resolve(strict=True)
            source.relative_to(artifacts_dir)
        except (FileNotFoundError, ValueError) as e:
            raise LocalWorkflowError(
                "attached copied artifact is not in this work's HK artifacts "
                f"directory: {record.artifact_path}"
            ) from e
        if raw_source.is_symlink() or source.is_symlink():
            raise LocalWorkflowError(
                f"attached copied artifact must not be a symlink: {record.artifact_path}"
            )
        if not source.is_file():
            raise LocalWorkflowError(
                f"attached artifact is missing from local HK state: {record.artifact_path}"
            )
        digest = file_sha256(source)
        if digest != record.sha256:
            raise LocalWorkflowError(
                "attached artifact content changed after attachment: "
                f"{record.artifact_path}"
            )
        rows.append((source, f"artifacts/{_artifact_export_filename(record)}", digest))
    return rows


def _handoff_dir_metadata(
    *,
    state: LocalState,
    work_dir: Path,
    output_path: Path,
    events: list[EventRecord],
    evidence: list[EvidenceRecord],
    readiness: ReadyResult,
    file_hashes: dict[str, str] | None = None,
) -> dict[str, object]:
    output_relative = _relative_to_root(output_path, state.target_root)
    artifact_exports = _attached_artifact_export_records(events)
    artifact_files = [
        str(row["export_path"]) for row in artifact_exports if row.get("export_path")
    ]
    return {
        "schema_version": 1,
        "generated_by": "hk export --format handoff-dir",
        "generated_at": datetime.now(UTC).isoformat(),
        "work_id": work_dir.name,
        "target_root": ".",
        "target_scope": _relative_to_root(state.target_scope, state.target_root),
        "branch": git_branch(state.target_root),
        "git_sha": git_sha(state.target_root),
        "dirty": git_dirty(state.target_root),
        "sync_status": sync_status_for(state),
        "ready_status": readiness.status,
        "ready": readiness.ready,
        "diff_hash": git_work_diff_hash(
            state.target_root,
            base_sha=work_start_git_sha(events),
            exclude_paths=work_freshness_excludes(work_dir, (output_relative,)),
        ),
        "event_count": _event_count(events),
        "event_seq": _max_event_seq(events),
        "evidence_count": len(evidence),
        "evidence_ids": [record.id for record in evidence],
        "output_path": output_relative,
        "files": [
            "README.md",
            "meta.json",
            "artifacts/README.md",
            *artifact_files,
        ],
        "attached_artifacts": artifact_exports,
        "file_hashes": file_hashes or {},
    }


def _stable_export_handoff_body(handoff_content: str) -> str:
    handoff_body = handoff_content.removeprefix("# Handoff\n\n")
    lines: list[str] = []
    section = ""
    for line in handoff_body.splitlines():
        if line.startswith("## "):
            section = line.removeprefix("## ").strip()
        if section == "Summary" and line.startswith(
            ("- Git SHA:", "- Dirty:", "- Sync status:")
        ):
            continue
        if section == "Readiness" and line.startswith(("- Status:", "- sync:")):
            continue
        lines.append(line)
    return "\n".join(lines) + "\n"


def _export_readme(
    work_id: str, handoff_content: str, output_relative: str, state: LocalState
) -> str:
    handoff_body = _stable_export_handoff_body(handoff_content)
    return (
        f"# HK export: `{work_id}`\n\n"
        "This directory is a generated review/handoff package from the Harness Kit "
        "ledger. Do not hand-edit it; update HK with `hk plan`, `hk decide`, "
        "`hk validate`, `hk review add`, and `hk sync`, then regenerate.\n\n"
        "## Freshness\n"
        "Validate this export against local HK state with:\n\n"
        "```bash\n"
        f"hk export --format handoff-dir --output {shlex.quote(output_relative)} --target .{_state_mode_arg(state)} --check\n"
        "```\n\n"
        "Historical hand-authored slice plans live under `.ai/plans/`; new "
        "Harness Toolkit repo work should use HK and generated `.ai/hk/` exports.\n\n"
        "## Handoff\n\n"
        f"{handoff_body}"
    )


def _artifacts_readme() -> str:
    return (
        "# Artifacts\n\n"
        "Artifacts are intentionally explicit. Raw validation transcripts stay in "
        "local/external HK state and are referenced from `README.md`; attach durable, "
        "reviewable files with `hk artifact attach` before export when they should be "
        "shared.\n"
    )


def _safe_export_relative(value: object) -> str | None:
    relative = str(value)
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts or not relative.strip():
        return None
    return path.as_posix()


def check_committed_handoff_exports(target: Path) -> list[Path]:
    """Validate committed handoff packages without requiring local HK ledger state."""
    target = target.resolve()
    ai_root = target / ".ai"
    exports_root = ai_root / "hk"
    if ai_root.is_symlink() or exports_root.is_symlink():
        raise LocalWorkflowError(
            f"HK export root must not have symlinked ancestors: {exports_root}"
        )
    if not exports_root.exists():
        return []
    if not exports_root.is_dir():
        raise LocalWorkflowError(f"HK export root must be a directory: {exports_root}")

    checked: list[Path] = []
    for destination in sorted(exports_root.iterdir()):
        if destination.is_symlink():
            raise LocalWorkflowError(
                f"HK export package must not be a symlink: {destination}"
            )
        if not destination.is_dir():
            continue
        meta_path = destination / "meta.json"
        if not meta_path.is_file() or meta_path.is_symlink():
            raise LocalWorkflowError(
                f"HK export metadata missing or unsafe: {meta_path}"
            )
        try:
            metadata = json.loads(meta_path.read_text())
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise LocalWorkflowError(
                f"invalid HK export metadata {meta_path}: {exc}"
            ) from exc
        if not isinstance(metadata, dict):
            raise LocalWorkflowError(
                f"invalid HK export metadata {meta_path}: expected JSON object"
            )

        expected_output = destination.relative_to(target).as_posix()
        if (
            metadata.get("schema_version") != 1
            or metadata.get("generated_by") != "hk export --format handoff-dir"
            or metadata.get("work_id") != destination.name
            or metadata.get("output_path") != expected_output
        ):
            raise LocalWorkflowError(
                f"HK export metadata identity is invalid: {meta_path}"
            )

        declared = metadata.get("files")
        if not isinstance(declared, list):
            raise LocalWorkflowError(
                f"HK export metadata files field is invalid: {meta_path}"
            )
        safe_files = [_safe_export_relative(item) for item in declared]
        if (
            any(path is None for path in safe_files)
            or len(set(safe_files)) != len(safe_files)
            or "meta.json" not in safe_files
        ):
            raise LocalWorkflowError(
                f"HK export metadata contains unsafe or duplicate files: {meta_path}"
            )
        expected_files = {path for path in safe_files if path is not None}

        symlinks: list[str] = []
        actual_files: set[str] = set()
        for path in destination.rglob("*"):
            relative = path.relative_to(destination).as_posix()
            if path.is_symlink():
                symlinks.append(relative)
            elif path.is_file():
                actual_files.add(relative)
        if symlinks:
            raise LocalWorkflowError(
                "HK export package contains symlinks: " + ", ".join(symlinks)
            )
        if actual_files != expected_files:
            missing = sorted(expected_files - actual_files)
            unexpected = sorted(actual_files - expected_files)
            details = []
            if missing:
                details.append("missing files: " + ", ".join(missing))
            if unexpected:
                details.append("unexpected files: " + ", ".join(unexpected))
            raise LocalWorkflowError(
                f"HK export file set is invalid at {destination}: " + "; ".join(details)
            )

        recorded_hashes = metadata.get("file_hashes")
        expected_hashed_files = expected_files - {"meta.json"}
        if (
            not isinstance(recorded_hashes, dict)
            or set(recorded_hashes) != expected_hashed_files
        ):
            raise LocalWorkflowError(
                f"HK export metadata file_hashes field is incomplete: {meta_path}"
            )
        for relative, recorded_hash in recorded_hashes.items():
            if _safe_export_relative(relative) != relative or not isinstance(
                recorded_hash, str
            ):
                raise LocalWorkflowError(
                    f"HK export metadata contains an unsafe file hash: {meta_path}"
                )
            actual_hash = _file_hash(destination / relative)
            if recorded_hash != actual_hash:
                raise LocalWorkflowError(
                    f"HK export file hash mismatch: {destination / relative}"
                )
        checked.append(destination)
    return checked


def _previous_export_files(destination: Path) -> set[str]:
    generated_names = {
        "AGENTS.md",
        "SUMMARY.md",
        "HANDOFF.md",
        "VALIDATION.md",
        "REVIEW.md",
        "DECISIONS.md",
        "META.json",
    }
    previous: set[str] = set()
    for metadata_name in ("meta.json", "META.json"):
        metadata_path = destination / metadata_name
        if not metadata_path.exists():
            continue
        try:
            metadata = json.loads(metadata_path.read_text())
        except json.JSONDecodeError:
            continue
        if not isinstance(metadata, dict):
            continue
        files = metadata.get("files", [])
        if isinstance(files, list):
            previous.update(
                relative for item in files if (relative := _safe_export_relative(item))
            )
    previous.update(name for name in generated_names if (destination / name).exists())
    return previous


def _remove_obsolete_export_files(destination: Path, keep: set[str]) -> None:
    destination_root = destination.resolve(strict=False)
    for relative in sorted(_previous_export_files(destination) - keep):
        path = destination / relative
        try:
            path.resolve(strict=False).relative_to(destination_root)
        except ValueError:
            continue
        if path.exists() and path.is_file():
            path.unlink()


def _sanitize_export_content(content: str, state: LocalState) -> str:
    root = str(state.target_root)
    sanitized = content.replace(root + "/", "").replace(root, ".")
    return re.sub(
        r"\.harness-local/[^`\s)]+",
        "<local HK state not exported>",
        sanitized,
    )


def _sanitize_export_artifact_paths(content: str, events: list[EventRecord]) -> str:
    sanitized = content
    for event in events:
        record = _artifact_record_from_event(event)
        if record is None:
            continue
        replacement = (
            f"artifacts/{_artifact_export_filename(record)}"
            if record.copied
            else "<referenced artifact not copied into export>"
        )
        for value in (record.artifact_path, record.source_path):
            if value:
                sanitized = sanitized.replace(value, replacement)
    return sanitized


def _compare_export_metadata(
    current: dict[str, object], recorded: dict[str, object]
) -> list[str]:
    ignored = {
        "generated_at",
        "dirty",
        "sync_status",
        "ready_status",
        "ready",
        "git_sha",
        "target_root",
        "target_scope",
        "file_hashes",
    }
    mismatches: list[str] = []
    for key, value in current.items():
        if key in ignored:
            continue
        if recorded.get(key) != value:
            mismatches.append(key)
    return mismatches


def _regenerate_export_hint(state: LocalState, destination: Path) -> str:
    return f"Try: regenerate with `{_handoff_export_commands(state, destination)['generate']}`."


def export_handoff_dir(
    target: Path,
    *,
    output_path: Path | None = None,
    check: bool = False,
    no_local_files: bool = False,
) -> ExportResult:
    state = ensure_state(target, no_local_files=no_local_files)
    work_dir = require_work(state)
    destination = output_path or (state.target_root / ".ai" / "hk" / work_dir.name)
    if not destination.is_absolute():
        destination = state.target_root / destination
    try:
        reject_symlink_ancestors(destination)
    except HandoffExportError as e:
        raise LocalWorkflowError(str(e)) from e
    output_relative = _relative_to_root(destination, state.target_root)
    export_freshness_excludes = (output_relative,)
    events = read_events(work_dir)
    evidence = read_evidence(work_dir)
    readiness = ready_for_work(
        work_dir,
        state,
        check_handoff=False,
        freshness_excludes=export_freshness_excludes,
    )
    artifact_files = _copied_artifacts_for_export(work_dir, events)
    expected_files = _expected_export_files(
        state,
        work_dir,
        output_relative=output_relative,
        events=events,
    )
    expected_file_hashes = {
        relative: _text_hash(content)
        for relative, content in expected_files.items()
        if relative != "README.md"
    }
    metadata = _handoff_dir_metadata(
        state=state,
        work_dir=work_dir,
        output_path=destination,
        events=events,
        evidence=evidence,
        readiness=readiness,
    )
    if check:
        status_result = _status_from_export_check_details(
            state,
            work_dir,
            destination,
            metadata,
            artifact_files,
            expected_file_hashes,
            expected_files,
        )
        if status_result.state != "fresh":
            raise LocalWorkflowError(
                status_result.message
                + "\n"
                + _regenerate_export_hint(state, destination)
            )
        return ExportResult(
            work_id=work_dir.name,
            path=str(destination),
            format="handoff-dir",
            checked=True,
            fresh=True,
            message="HK export is fresh",
        )

    destination.parent.mkdir(parents=True, exist_ok=True)
    prepare_generated_directory(destination)
    artifacts_dir = destination / "artifacts"
    prepare_generated_directory(artifacts_dir)
    files = dict(expected_files)
    file_hashes = {relative: _text_hash(content) for relative, content in files.items()}
    file_hashes.update({relative: digest for _, relative, digest in artifact_files})
    metadata = _handoff_dir_metadata(
        state=state,
        work_dir=work_dir,
        output_path=destination,
        events=events,
        evidence=evidence,
        readiness=readiness,
        file_hashes=file_hashes,
    )
    files["meta.json"] = json.dumps(metadata, indent=2, sort_keys=True) + "\n"
    keep_files = set(files) | {relative for _, relative, _ in artifact_files}
    _remove_obsolete_export_files(destination, keep_files)
    for relative, content in files.items():
        path = destination / relative
        try:
            safe_write_generated_file(path, content)
        except HandoffExportError as e:
            raise LocalWorkflowError(str(e)) from e
    for source, relative, _ in artifact_files:
        try:
            safe_copy_generated_file(source, destination / relative)
        except HandoffExportError as e:
            raise LocalWorkflowError(str(e)) from e

    refreshed_readiness = ready_for_work(
        work_dir,
        state,
        check_handoff=False,
        freshness_excludes=export_freshness_excludes,
    )
    refreshed_files = _expected_export_files(
        state,
        work_dir,
        output_relative=output_relative,
        events=events,
    )
    if refreshed_files != expected_files:
        files = dict(refreshed_files)
        file_hashes = {
            relative: _text_hash(content) for relative, content in files.items()
        }
        file_hashes.update({relative: digest for _, relative, digest in artifact_files})
        metadata = _handoff_dir_metadata(
            state=state,
            work_dir=work_dir,
            output_path=destination,
            events=events,
            evidence=evidence,
            readiness=refreshed_readiness,
            file_hashes=file_hashes,
        )
        files["meta.json"] = json.dumps(metadata, indent=2, sort_keys=True) + "\n"
        for relative, content in files.items():
            try:
                safe_write_generated_file(destination / relative, content)
            except HandoffExportError as e:
                raise LocalWorkflowError(str(e)) from e
    return ExportResult(
        work_id=work_dir.name,
        path=str(destination),
        format="handoff-dir",
        message="HK handoff directory exported",
    )


def init_spec(target: Path, *, no_local_files: bool = False) -> SpecResult:
    state = ensure_state(target, no_local_files=no_local_files)
    try:
        return init_spec_for_state(state)
    except SpecWorkflowError as e:
        raise LocalWorkflowError(str(e)) from e


def spec_status(target: Path, *, no_local_files: bool = False) -> SpecResult:
    state = resolve_local_state(target, no_local_files=no_local_files)
    try:
        return spec_status_for_state(state)
    except SpecWorkflowError as e:
        raise LocalWorkflowError(str(e)) from e


def spec_outline(target: Path, *, no_local_files: bool = False) -> SpecOutline:
    state = resolve_local_state(target, no_local_files=no_local_files)
    try:
        return spec_outline_for_state(state)
    except SpecWorkflowError as e:
        raise LocalWorkflowError(str(e)) from e


def spec_promote_dry_run(target: Path, *, no_local_files: bool = False) -> str:
    state = resolve_local_state(target, no_local_files=no_local_files)
    try:
        return spec_promote_dry_run_for_state(state)
    except SpecWorkflowError as e:
        raise LocalWorkflowError(str(e)) from e


def json_dump_dataclass(value: JsonDataclass) -> str:
    return json.dumps(asdict(value), indent=2, sort_keys=True)


def json_dump_object(value: object) -> str:
    return json.dumps(value, indent=2, sort_keys=True)


def print_capture_and_exit(result: CaptureResult) -> None:
    print(json_dump_dataclass(result))
    if result.exit_code != 0:
        raise SystemExit(result.exit_code)

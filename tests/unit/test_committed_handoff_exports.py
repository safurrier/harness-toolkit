"""Static integrity checks for committed HK handoff packages."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import cast

import pytest

from harness_toolkit.kit.local import (
    LocalWorkflowError,
    check_committed_handoff_exports,
)

pytestmark = pytest.mark.unit


def _digest(content: bytes) -> str:
    return "sha256:" + hashlib.sha256(content).hexdigest()


def make_export(root: Path, name: str) -> Path:
    destination = root / ".ai" / "hk" / name
    (destination / "artifacts").mkdir(parents=True)
    files = {
        "README.md": f"# {name}\n".encode(),
        "artifacts/README.md": b"# Artifacts\n",
    }
    for relative, content in files.items():
        (destination / relative).write_bytes(content)
    metadata = {
        "schema_version": 1,
        "generated_by": "hk export --format handoff-dir",
        "work_id": name,
        "output_path": f".ai/hk/{name}",
        "files": ["README.md", "meta.json", "artifacts/README.md"],
        "file_hashes": {
            relative: _digest(content) for relative, content in files.items()
        },
    }
    (destination / "meta.json").write_text(json.dumps(metadata) + "\n")
    return destination


def metadata_for(destination: Path) -> dict[str, object]:
    return json.loads((destination / "meta.json").read_text())


def write_metadata(destination: Path, metadata: dict[str, object]) -> None:
    (destination / "meta.json").write_text(json.dumps(metadata) + "\n")


def test_checks_every_committed_export_without_local_ledger(tmp_path: Path) -> None:
    first = make_export(tmp_path, "2026-01-01-first")
    second = make_export(tmp_path, "2026-01-02-second")
    (tmp_path / ".ai" / "hk" / "AGENTS.md").write_text("# Guidance\n")

    assert check_committed_handoff_exports(tmp_path) == [first, second]
    assert not (tmp_path / ".harness-local").exists()


def test_rejects_modified_export_file(tmp_path: Path) -> None:
    destination = make_export(tmp_path, "2026-01-01-demo")
    (destination / "README.md").write_text("tampered\n")

    with pytest.raises(LocalWorkflowError, match="file hash mismatch"):
        check_committed_handoff_exports(tmp_path)


def test_rejects_incomplete_hash_inventory(tmp_path: Path) -> None:
    destination = make_export(tmp_path, "2026-01-01-demo")
    metadata = metadata_for(destination)
    hashes = cast(dict[str, object], metadata["file_hashes"])
    hashes.pop("README.md")
    write_metadata(destination, metadata)

    with pytest.raises(LocalWorkflowError, match="file_hashes field is incomplete"):
        check_committed_handoff_exports(tmp_path)


def test_rejects_unsafe_declared_path(tmp_path: Path) -> None:
    destination = make_export(tmp_path, "2026-01-01-demo")
    metadata = metadata_for(destination)
    files = cast(list[object], metadata["files"])
    files.append("../outside")
    write_metadata(destination, metadata)

    with pytest.raises(LocalWorkflowError, match="unsafe or duplicate files"):
        check_committed_handoff_exports(tmp_path)


def test_rejects_unexpected_export_file(tmp_path: Path) -> None:
    destination = make_export(tmp_path, "2026-01-01-demo")
    (destination / "extra.txt").write_text("unexpected\n")

    with pytest.raises(LocalWorkflowError, match="unexpected files: extra.txt"):
        check_committed_handoff_exports(tmp_path)


def test_rejects_symlink_in_export(tmp_path: Path) -> None:
    destination = make_export(tmp_path, "2026-01-01-demo")
    (destination / "README.md").unlink()
    (destination / "README.md").symlink_to(tmp_path / "outside")

    with pytest.raises(LocalWorkflowError, match="contains symlinks: README.md"):
        check_committed_handoff_exports(tmp_path)


def test_rejects_symlinked_export_package(tmp_path: Path) -> None:
    exports = tmp_path / ".ai" / "hk"
    exports.mkdir(parents=True)
    (exports / "linked-package").symlink_to(tmp_path / "outside")

    with pytest.raises(LocalWorkflowError, match="package must not be a symlink"):
        check_committed_handoff_exports(tmp_path)


def test_rejects_broken_export_ancestor_symlink(tmp_path: Path) -> None:
    (tmp_path / ".ai").symlink_to(tmp_path / "missing-ai-root")

    with pytest.raises(LocalWorkflowError, match="symlinked ancestors"):
        check_committed_handoff_exports(tmp_path)


def test_rejects_metadata_for_another_output(tmp_path: Path) -> None:
    destination = make_export(tmp_path, "2026-01-01-demo")
    metadata = metadata_for(destination)
    metadata["output_path"] = ".ai/hk/another-package"
    write_metadata(destination, metadata)

    with pytest.raises(LocalWorkflowError, match="metadata identity is invalid"):
        check_committed_handoff_exports(tmp_path)

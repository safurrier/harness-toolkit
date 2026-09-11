"""Unit tests for shared mise task helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.lib import product_verification_assets

pytestmark = pytest.mark.unit


def test_product_verification_assets_allows_both_absent(tmp_path: Path) -> None:
    assert product_verification_assets(tmp_path) is None


def test_product_verification_assets_returns_regular_pair(tmp_path: Path) -> None:
    config = tmp_path / ".harness" / "verification.toml"
    runner = tmp_path / "scripts" / "verify-routes"
    config.parent.mkdir()
    runner.parent.mkdir()
    config.write_text("version = 1\n")
    runner.write_text("#!/bin/sh\n")

    assert product_verification_assets(tmp_path) == (config, runner)


@pytest.mark.parametrize("link_both", [False, True])
def test_product_verification_assets_rejects_broken_links(
    tmp_path: Path, link_both: bool
) -> None:
    config = tmp_path / ".harness" / "verification.toml"
    runner = tmp_path / "scripts" / "verify-routes"
    config.parent.mkdir()
    runner.parent.mkdir()
    config.symlink_to(tmp_path / "missing-config")
    if link_both:
        runner.symlink_to(tmp_path / "missing-runner")

    with pytest.raises(RuntimeError, match="must both be regular files"):
        product_verification_assets(tmp_path)


def test_product_verification_assets_rejects_symlinked_runner(tmp_path: Path) -> None:
    config = tmp_path / ".harness" / "verification.toml"
    runner = tmp_path / "scripts" / "verify-routes"
    config.parent.mkdir()
    runner.parent.mkdir()
    config.write_text("version = 1\n")
    external = tmp_path / "external-runner"
    external.write_text("#!/bin/sh\n")
    runner.symlink_to(external)

    with pytest.raises(RuntimeError, match="must both be regular files"):
        product_verification_assets(tmp_path)


@pytest.mark.parametrize("linked_parent", [".harness", "scripts"])
def test_product_verification_assets_rejects_symlinked_parent(
    tmp_path: Path, linked_parent: str
) -> None:
    external = tmp_path / f"external-{linked_parent.removeprefix('.')}"
    external.mkdir()
    (tmp_path / linked_parent).symlink_to(external)
    other_parent = "scripts" if linked_parent == ".harness" else ".harness"
    (tmp_path / other_parent).mkdir()
    (tmp_path / ".harness" / "verification.toml").write_text("version = 1\n")
    (tmp_path / "scripts" / "verify-routes").write_text("#!/bin/sh\n")

    with pytest.raises(RuntimeError, match="must both be regular files"):
        product_verification_assets(tmp_path)

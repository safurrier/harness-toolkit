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

"""End-to-end proof that a generated browser route drives visible behavior."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from tests._support import init_project, mise

pytestmark = [pytest.mark.e2e, pytest.mark.slow]


def _configure_browser_route(project: Path) -> None:
    route = project / "scripts" / "verify" / "threejs-browser-journey"
    route.parent.mkdir(parents=True)
    route.write_text("#!/bin/sh\nexec npm run e2e\n")
    route.chmod(0o755)
    (project / ".harness" / "verification.toml").write_text(
        """version = 1
[[routes]]
id = "threejs-browser-journey"
paths = ["src/**", "test/e2e.mjs"]
script = "scripts/verify/threejs-browser-journey"
required = true
kind = "browser"
"""
    )


def test_generated_threejs_browser_route_observes_journey_and_negative_control(
    scaffold_copy: Path,
) -> None:
    """A browser route must fail when the observed precondition is corrupted."""
    result = init_project(
        scaffold_copy,
        name="threejs-verification",
        shape="single",
        stack="threejs",
    )
    assert result.returncode == 0, result.stderr

    setup = mise("setup", scaffold_copy, timeout=300)
    assert setup.returncode == 0, setup.stderr
    _configure_browser_route(scaffold_copy)

    verified = subprocess.run(
        ["scripts/verify-routes", "--path", "src/main.js"],
        cwd=scaffold_copy,
        text=True,
        capture_output=True,
        timeout=300,
    )
    assert verified.returncode == 0, verified.stderr
    assert "Verified 1 required route(s)." in verified.stdout
    assert (scaffold_copy / "test-results" / "portrait-delivered.png").is_file()

    main = scaffold_copy / "src" / "main.js"
    original = main.read_text()
    corrupted = original.replace(
        "state = { apples: [], delivered: false },",
        'state = { apples: ["unexpected"], delivered: false },',
        1,
    )
    assert corrupted != original
    main.write_text(corrupted)
    negative = subprocess.run(
        ["scripts/verify-routes", "--path", "src/main.js"],
        cwd=scaffold_copy,
        text=True,
        capture_output=True,
        timeout=300,
    )
    assert negative.returncode != 0
    assert "negative control collected an apple without reaching one" in negative.stderr

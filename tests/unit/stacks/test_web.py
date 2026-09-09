"""Unit tests for WebStack."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit


def test_tools_toml_has_node_python_and_uv() -> None:
    from harness_toolkit.scaffold.stacks.web import WebStack

    tools = WebStack().tools_toml()
    assert 'python = "3.12"' in tools
    assert 'uv = "latest"' in tools
    assert 'node = "22"' in tools
    assert 'npm = "11.6.2"' in tools


def test_web_dev_dependencies_pin_compatible_peer_sets() -> None:
    from harness_toolkit.scaffold.config import Config
    from harness_toolkit.scaffold.stacks.web import _web_dev_dependencies

    dependencies = _web_dev_dependencies(
        Config("webprobe", "A generated web app", "single", "web")
    )

    assert dependencies["vitest"] == "4.1.11"
    assert dependencies["@vitest/browser-playwright"] == "4.1.11"
    assert dependencies["wrangler"] == "4.130.0"
    assert dependencies["@cloudflare/workers-types"] == "5.20260908.1"


def test_adr_notes_mentions_key_tools() -> None:
    from harness_toolkit.scaffold.stacks.web import WebStack

    notes = WebStack().adr_notes()
    assert "Vite" in notes
    assert "TypeScript" in notes
    assert "Cloudflare Workers" in notes
    assert "D1" in notes
    assert "Vitest" in notes


def test_stack_notes_mentions_key_tools() -> None:
    from harness_toolkit.scaffold.stacks.web import WebStack

    notes = WebStack().stack_notes()
    assert "prettier" in notes
    assert "eslint" in notes
    assert "tsc --noEmit" in notes
    assert "vitest" in notes
    assert "wrangler deploy --dry-run" in notes


def test_init_single_escapes_description_for_tsx(tmp_path: Path) -> None:
    from harness_toolkit.scaffold.config import Config
    from harness_toolkit.scaffold.stacks.web import WebStack

    config = Config(
        name="webprobe",
        description='A < B & {C} "quoted" `tick` ${value}',
        shape="single",
        stack="web",
    )
    WebStack().init_single(tmp_path, config)

    app = (tmp_path / "src" / "app" / "App.tsx").read_text()
    assert (
        '<p className="summary">{`A < B & {C} "quoted" \\`tick\\` \\${value}`}</p>'
        in app
    )


def test_generated_web_manifest_overrides_only_transitive_sharp(tmp_path: Path) -> None:
    from harness_toolkit.scaffold.config import Config
    from harness_toolkit.scaffold.stacks.web import WebStack

    WebStack().init_single(
        tmp_path,
        Config("webprobe", "A generated web app", "single", "web"),
    )

    manifest = json.loads((tmp_path / "package.json").read_text())
    assert manifest["overrides"]["sharp"] == "0.35.4"
    assert "sharp" not in manifest["dependencies"]


def test_tailwind_variant_adds_tailwind_tooling(tmp_path: Path) -> None:
    from harness_toolkit.scaffold.config import Config
    from harness_toolkit.scaffold.stacks.web import WebStack

    config = Config(
        name="webprobe",
        description="A generated web app",
        shape="single",
        stack="web",
        web_ui="tailwind",
    )
    WebStack().init_single(tmp_path, config)

    package_json = (tmp_path / "package.json").read_text()
    assert '"@tailwindcss/vite"' in package_json
    assert '"tailwindcss"' in package_json
    assert "tailwindcss()" in (tmp_path / "vite.config.ts").read_text()
    assert '@import "tailwindcss";' in (tmp_path / "src" / "styles.css").read_text()


def test_shadcn_variant_adds_components_and_tailwind(tmp_path: Path) -> None:
    from harness_toolkit.scaffold.config import Config
    from harness_toolkit.scaffold.stacks.web import WebStack

    config = Config(
        name="webprobe",
        description="A generated web app",
        shape="single",
        stack="web",
        web_ui="shadcn",
    )
    WebStack().init_single(tmp_path, config)

    assert (tmp_path / "components.json").exists()
    assert (tmp_path / "src" / "lib" / "utils.ts").exists()
    assert (tmp_path / "src" / "components" / "ui" / "button.tsx").exists()
    assert (
        "@/components/ui/button" in (tmp_path / "src" / "app" / "App.tsx").read_text()
    )
    package_json = (tmp_path / "package.json").read_text()
    assert '"class-variance-authority"' in package_json
    assert '"tailwindcss"' in package_json


def test_drizzle_d1_variant_adds_schema_and_drizzle_queries(tmp_path: Path) -> None:
    from harness_toolkit.scaffold.config import Config
    from harness_toolkit.scaffold.stacks.web import WebStack

    config = Config(
        name="webprobe",
        description="A generated web app",
        shape="single",
        stack="web",
        web_db="drizzle-d1",
    )
    WebStack().init_single(tmp_path, config)

    assert (tmp_path / "worker" / "db" / "schema.ts").exists()
    saved_runs = (tmp_path / "worker" / "db" / "savedRuns.ts").read_text()
    assert 'from "drizzle-orm/d1"' in saved_runs
    assert "drizzle(db)" in saved_runs
    assert '"drizzle-orm"' in (tmp_path / "package.json").read_text()


def test_remove_examples_rewrites_app_without_example_import(tmp_path: Path) -> None:
    from harness_toolkit.scaffold.config import Config
    from harness_toolkit.scaffold.stacks.web import WebStack

    app_dir = tmp_path / "src" / "app"
    tests_dir = tmp_path / "tests"
    app_dir.mkdir(parents=True)
    tests_dir.mkdir()
    (app_dir / "App.tsx").write_text(
        'import { ExamplePanel } from "./ExamplePanel";\n'
        "export function App() { return <ExamplePanel />; }\n"
    )
    (app_dir / "ExamplePanel.tsx").write_text(
        "export function ExamplePanel() { return null; }\n"
    )
    (tests_dir / "app.test.ts").write_text("export {};\n")

    config = Config(
        name="webprobe",
        description='A < B & {C} "quoted" `tick` ${value}',
        shape="single",
        stack="web",
    )
    WebStack().remove_examples(tmp_path, config)

    app = (app_dir / "App.tsx").read_text()
    assert "ExamplePanel" not in app
    assert "webprobe" in app
    assert (
        '<p className="summary">{`A < B & {C} "quoted" \\`tick\\` \\${value}`}</p>'
        in app
    )
    assert not (app_dir / "ExamplePanel.tsx").exists()
    assert not (tests_dir / "app.test.ts").exists()

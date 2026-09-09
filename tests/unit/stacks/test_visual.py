"""Unit tests for the explicit visual starter stacks."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from harness_toolkit.scaffold.config import Config
from harness_toolkit.scaffold.stacks.blender import BlenderStack
from harness_toolkit.scaffold.stacks.threejs import ThreejsStack

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("stack", "expected"),
    [(BlenderStack(), "scene.py"), (ThreejsStack(), "src/main.js")],
)
def test_visual_stacks_copy_editable_single_project_sources(
    tmp_path: Path, stack: BlenderStack | ThreejsStack, expected: str
) -> None:
    config = Config(
        name="visual-probe",
        description="A visual probe",
        shape="single",
        stack="blender" if isinstance(stack, BlenderStack) else "threejs",
    )

    stack.init_single(tmp_path, config)

    assert (tmp_path / expected).exists()


def test_blender_generated_lock_is_rendered_for_arbitrary_valid_name(
    tmp_path: Path,
) -> None:
    BlenderStack().init_single(
        tmp_path,
        Config("arbitrary-valid-name", "A scene", "single", "blender"),
    )

    lock = (tmp_path / "uv.lock").read_text()
    assert 'name = "arbitrary-valid-name"' in lock
    assert "{{ project_name }}" not in lock
    assert 'name = "harness-toolkit"' not in lock


def test_blender_source_has_node_materials_and_reference_brief(tmp_path: Path) -> None:
    BlenderStack().init_single(
        tmp_path,
        Config("scene-probe", "A scene", "single", "blender"),
    )

    scene = (tmp_path / "scene.py").read_text()
    assert "BRIEF" in scene
    assert "result.use_nodes = True" in scene
    assert "BLENDER_EEVEE_NEXT" in scene


def test_blender_setup_and_dev_tasks_use_locked_python_scene_execution() -> None:
    root = Path(__file__).resolve().parents[3]
    task_dir = root / ".mise" / "tasks"
    setup = (task_dir / "setup").read_text()
    dev = (task_dir / "dev").read_text()

    for task in ("build", "dev", "fmt", "lint", "setup", "test", "typecheck", "verify"):
        assert (
            (task_dir / task)
            .read_text()
            .startswith("#!/usr/bin/env -S env UV_NO_CONFIG=1 uv run python")
        )
    assert setup.startswith("#!/usr/bin/env -S env UV_NO_CONFIG=1 uv run python")
    assert 'run(["uv", "sync", "--locked", "--all-groups"], cwd=cwd)' in setup
    assert 'command = [blender, "--python", "scene.py"]' in dev
    assert 'command = [blender, "scene.blend"]' in dev


def test_threejs_tools_include_the_managed_task_runtime() -> None:
    tools = ThreejsStack().tools_toml()

    assert 'python = "3.12"' in tools
    assert 'uv = "latest"' in tools
    assert 'node = "22"' in tools


def test_blender_build_requires_finished_operators_and_verify_checks_artifacts() -> (
    None
):
    root = Path(__file__).resolve().parents[3]
    build_source = (root / "stacks" / "blender" / "build.py").read_text()
    assert build_source.startswith(
        "import runpy\nfrom pathlib import Path\n\nimport bpy\n\n"
    )
    helper = next(
        node
        for node in ast.parse(build_source).body
        if isinstance(node, ast.FunctionDef) and node.name == "require_finished"
    )
    namespace: dict[str, object] = {}
    exec(
        compile(ast.Module(body=[helper], type_ignores=[]), "build.py", "exec"),
        namespace,
    )
    require_finished = namespace["require_finished"]
    require_finished({"FINISHED"}, "save")  # type: ignore[operator]
    with pytest.raises(RuntimeError, match="render"):
        require_finished({"CANCELLED"}, "render")  # type: ignore[operator]

    assert build_source.index("scene.render.filepath") < build_source.index(
        "save_as_mainfile"
    )
    task = (root / ".mise" / "tasks" / "verify").read_text()
    assert task.count('"--factory-startup"') >= 2
    assert 'png.read_bytes()[:8] != b"\\x89PNG\\r\\n\\x1a\\n"' in task
    assert "nonempty scene.blend" in task
    assert "nonempty scene.png" in task


def test_threejs_template_has_loopback_dev_and_context_recovery(tmp_path: Path) -> None:
    ThreejsStack().init_single(
        tmp_path,
        Config("game-probe", "A game", "single", "threejs"),
    )

    manifest = (tmp_path / "package.json").read_text()
    readme = (tmp_path / "README.md").read_text()
    source = (tmp_path / "src" / "main.js").read_text()
    e2e = (tmp_path / "test" / "e2e.mjs").read_text()
    assert '"dev": "vite"' in manifest
    assert '"dev:lan": "vite --host 0.0.0.0"' in manifest
    assert "trusted-LAN" in readme
    assert 'canvas.addEventListener("webglcontextlost"' in source
    assert 'canvas.addEventListener("webglcontextrestored"' in source
    assert "event.preventDefault()" in source
    assert "paused = true" in source
    assert "resetAll()" in source
    assert "resize();" in source
    assert "__visualPrototypeLoseContextExtension = extension" in e2e
    assert "__visualPrototypeLoseContextExtension.restoreContext()" in e2e
    assert 'getExtension("WEBGL_lose_context").restoreContext()' not in e2e


def test_threejs_template_has_lockfile_and_mobile_safety_seams(tmp_path: Path) -> None:
    ThreejsStack().init_single(
        tmp_path,
        Config("game-probe", "A game", "single", "threejs"),
    )

    assert (tmp_path / "package-lock.json").exists()
    index = (tmp_path / "index.html").read_text()
    source = (tmp_path / "src" / "main.js").read_text()
    assert 'charset="utf-8"' in index
    assert "visualPrototypeTelemetry" in source
    assert "pointercancel" in source
    assert (tmp_path / "src" / "style.local.css").exists()


@pytest.mark.parametrize("stack", [BlenderStack(), ThreejsStack()])
def test_visual_stacks_reject_apps_and_example_removal(
    stack: BlenderStack | ThreejsStack,
) -> None:
    config = Config("visual-probe", "A visual probe", "apps", "blender")
    with pytest.raises(ValueError, match="only --shape single"):
        stack.init_module(Path("unused"), config, "app")
    with pytest.raises(ValueError, match="--no-examples"):
        stack.remove_examples(Path("unused"), config)

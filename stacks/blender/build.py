import runpy
from pathlib import Path

import bpy


def require_finished(result: set[str], operation: str) -> None:
    if "FINISHED" not in result:
        raise RuntimeError(f"Blender {operation} did not finish: {result}")


root = Path.cwd()
scene_module = runpy.run_path(str(root / "scene.py"), run_name="visual_scene")
scene_module["build"]()
bpy.context.scene.render.filepath = str(root / "scene.png")
require_finished(
    bpy.ops.wm.save_as_mainfile(filepath=str(root / "scene.blend")), "save"
)
require_finished(bpy.ops.render.render(write_still=True), "render")

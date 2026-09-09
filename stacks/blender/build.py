from pathlib import Path
import runpy

import bpy

root = Path.cwd()
scene_module = runpy.run_path(str(root / "scene.py"), run_name="visual_scene")
scene_module["build"]()
bpy.ops.wm.save_as_mainfile(filepath=str(root / "scene.blend"))
bpy.context.scene.render.filepath = str(root / "scene.png")
bpy.ops.render.render(write_still=True)

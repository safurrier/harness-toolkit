"""Editable Blender scene source."""

import math

import bpy
from mathutils import Vector

# EDIT SEAM: replace this brief and arrangement with your own scene.
BRIEF = "A cheerful robot gardener watering three colorful pots at sunrise."


def material(name, color, metallic=0.0):
    result = bpy.data.materials.new(name)
    result.use_nodes = True
    result.diffuse_color = (*color, 1)
    result.metallic = metallic
    result.roughness = 0.42
    principled = result.node_tree.nodes["Principled BSDF"]
    principled.inputs["Base Color"].default_value = (*color, 1)
    principled.inputs["Metallic"].default_value = metallic
    principled.inputs["Roughness"].default_value = 0.42
    return result


def cube(name, location, scale, surface, bevel=0.12):
    bpy.ops.mesh.primitive_cube_add(location=location)
    result = bpy.context.object
    result.name = name
    result.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    modifier = result.modifiers.new("soft edges", "BEVEL")
    modifier.width = bevel
    modifier.segments = 3
    result.data.materials.append(surface)
    return result


def sphere(name, location, scale, surface):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, location=location)
    result = bpy.context.object
    result.name = name
    result.scale = scale
    result.data.materials.append(surface)
    return result


def build():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    teal = material("robot teal", (0.03, 0.45, 0.48), 0.35)
    cream = material("ceramic cream", (0.95, 0.68, 0.25))
    colors = [
        material("pot coral", (0.9, 0.12, 0.06)),
        material("pot blue", (0.08, 0.3, 0.9)),
        material("pot pink", (0.95, 0.12, 0.48)),
    ]
    cube(
        "ground",
        (0, 0, -0.2),
        (7, 7, 0.2),
        material("garden ground", (0.08, 0.18, 0.12)),
        0.02,
    )
    for x, color in zip((-2, 0, 2), colors, strict=True):
        bpy.ops.mesh.primitive_cone_add(
            vertices=32, radius1=0.72, radius2=0.52, depth=0.9, location=(x, 1, 0.45)
        )
        pot = bpy.context.object
        pot.name = "colorful flower pot"
        pot.data.materials.append(color)
        sphere(
            "plant",
            (x, 1, 1.3),
            (0.34, 0.34, 0.5),
            material(f"leaf{x}", (0.12, 0.62, 0.2)),
        )
    cube("robot body", (0, -1, 0.9), (0.55, 0.38, 0.65), teal)
    sphere("robot head", (0, -1, 1.75), (0.52, 0.42, 0.42), cream)
    cube(
        "visor",
        (0, -1.43, 1.75),
        (0.34, 0.04, 0.12),
        material("visor", (0.02, 0.04, 0.08)),
        0.03,
    )
    cube("watering can", (1, -0.8, 0.85), (0.42, 0.23, 0.3), cream)
    cube("spout", (1.5, -0.8, 0.9), (0.35, 0.12, 0.1), cream, 0.04)
    bpy.ops.object.light_add(type="AREA", location=(3, -4, 6))
    bpy.context.object.data.energy = 1100
    bpy.context.object.data.shape = "DISK"
    bpy.context.object.data.size = 5
    bpy.ops.object.light_add(type="SUN", location=(0, 0, 5))
    bpy.context.object.data.energy = 1.2
    bpy.context.object.rotation_euler = (
        math.radians(25),
        math.radians(-20),
        math.radians(25),
    )
    bpy.ops.object.camera_add(location=(6, -9, 5))
    camera = bpy.context.object
    bpy.context.scene.camera = camera
    camera.rotation_euler = (math.radians(67), 0, math.radians(34))
    camera.rotation_euler = (
        (Vector((0, 0, 1)) - camera.location).to_track_quat("-Z", "Y").to_euler()
    )
    scene = bpy.context.scene
    engines = scene.render.bl_rna.properties["engine"].enum_items.keys()
    scene.render.engine = (
        "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in engines else "BLENDER_EEVEE"
    )
    scene.render.resolution_x = 800
    scene.render.resolution_y = 600
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.world.color = (0.03, 0.04, 0.08)


if __name__ == "__main__":
    build()

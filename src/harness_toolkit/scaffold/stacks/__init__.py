"""Stack registry — maps stack name to Stack instance."""

from __future__ import annotations

from harness_toolkit.scaffold.stacks.blender import BlenderStack
from harness_toolkit.scaffold.stacks.go import GoStack
from harness_toolkit.scaffold.stacks.python import PythonStack
from harness_toolkit.scaffold.stacks.rust import RustStack
from harness_toolkit.scaffold.stacks.threejs import ThreejsStack
from harness_toolkit.scaffold.stacks.web import WebStack

STACKS: dict[
    str, PythonStack | GoStack | RustStack | WebStack | BlenderStack | ThreejsStack
] = {
    "python": PythonStack(),
    "go": GoStack(),
    "rust": RustStack(),
    "web": WebStack(),
    "blender": BlenderStack(),
    "threejs": ThreejsStack(),
}

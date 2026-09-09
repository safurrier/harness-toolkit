"""Blender visual-scene stack implementation."""

from __future__ import annotations

import shutil
from pathlib import Path

from harness_toolkit.scaffold.config import SCAFFOLD_ROOT, Config
from harness_toolkit.scaffold.templates import copy_tree, render_template


class BlenderStack:
    def tools_toml(self) -> str:
        return 'python = "3.12"\nuv = "latest"\n'

    def adr_notes(self) -> str:
        return """\
The Blender stack uses Blender's Python API for an editable local scene.
Blender is discovered from `BLENDER_BIN` or `PATH`; renders save both `.blend`
and `.png` artifacts."""

    def stack_notes(self) -> str:
        return """\
- Editable scene source: `scene.py` (including a reference brief)
- Render: Blender background mode with `--python-exit-code 1`
- Source checks: ruff, Python syntax compilation, pytest
- Verification: render and reopen `scene.blend` when Blender is installed"""

    def init_single(self, root: Path, config: Config) -> dict[str, str]:
        context = {
            "project_name": config.name,
            "project_description": config.description,
        }
        stack_dir = SCAFFOLD_ROOT / "stacks" / "blender"
        tests_dir = root / "tests"
        if tests_dir.exists():
            shutil.rmtree(tests_dir)
        copy_tree(stack_dir, root, context)
        _write(stack_dir / "pyproject.toml.tmpl", root / "pyproject.toml", context)
        return {
            "project_structure": _single_structure(config.name),
            "stack_notes": self.stack_notes(),
            "stack_adr_notes": self.adr_notes(),
        }

    def init_module(
        self, mod_dir: Path, config: Config, mod_name: str
    ) -> dict[str, str]:
        raise ValueError("The Blender stack supports only --shape single")

    def remove_examples(self, root: Path, config: Config) -> None:
        raise ValueError(
            "--no-examples is not supported for the Blender visual starter"
        )

    def remove_module_examples(self, mod_dir: Path) -> None:
        raise ValueError("The Blender stack supports only --shape single")


def _write(src: Path, dst: Path, context: dict[str, str]) -> None:
    dst.write_text(render_template(src, context))


def _single_structure(project_name: str) -> str:
    return f"""\
```
{project_name}/
├── scene.py              # Editable scene and reference brief
├── build.py              # Blender build entrypoint
├── scene.blend           # Generated editable Blender file
├── scene.png             # Generated render
└── tests/                # Source-layout tests
```"""

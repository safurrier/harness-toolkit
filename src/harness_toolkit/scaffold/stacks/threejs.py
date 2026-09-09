"""Backend-free Three.js visual starter stack."""

from __future__ import annotations

import shutil
from pathlib import Path

from harness_toolkit.scaffold.config import SCAFFOLD_ROOT, Config
from harness_toolkit.scaffold.templates import copy_tree


class ThreejsStack:
    def tools_toml(self) -> str:
        return 'python = "3.12"\nuv = "latest"\nnode = "22"\n'

    def adr_notes(self) -> str:
        return """\
The Three.js stack is a backend-free Vite application with local dependencies,
mobile-safe touch controls, CSS override seam, native Node unit tests, and an
optional Playwright browser verification route."""

    def stack_notes(self) -> str:
        return """\
- Runtime: Vite + Three.js, served locally without a backend
- Formatter/linter/typecheck: prettier, eslint, tsc
- Tests: native `node --test`; browser E2E uses Playwright when Chromium is available
- Edit seams: `src/main.js` world geometry and `src/style.local.css` overrides"""

    def init_single(self, root: Path, config: Config) -> dict[str, str]:
        context = {
            "project_name": config.name,
            "project_description": config.description,
        }
        stack_dir = SCAFFOLD_ROOT / "stacks" / "threejs"
        tests_dir = root / "tests"
        if tests_dir.exists():
            shutil.rmtree(tests_dir)
        copy_tree(stack_dir, root, context)
        return {
            "project_structure": _single_structure(config.name),
            "stack_notes": self.stack_notes(),
            "stack_adr_notes": self.adr_notes(),
        }

    def init_module(
        self, mod_dir: Path, config: Config, mod_name: str
    ) -> dict[str, str]:
        raise ValueError("The Three.js stack supports only --shape single")

    def remove_examples(self, root: Path, config: Config) -> None:
        raise ValueError(
            "--no-examples is not supported for the Three.js visual starter"
        )

    def remove_module_examples(self, mod_dir: Path) -> None:
        raise ValueError("The Three.js stack supports only --shape single")


def _single_structure(project_name: str) -> str:
    return f"""\
```
{project_name}/
├── src/main.js           # Editable Three.js world and controls
├── src/style.local.css   # CSS-first local override seam
├── test/                 # Native rules and browser E2E tests
├── package-lock.json     # Reproducible local dependencies
└── index.html            # Mobile viewport entrypoint
```"""

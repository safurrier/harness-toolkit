"""Project configuration dataclass and validation utilities."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

# Source checkouts use the repository root. Wheels bundle the runtime scaffold files
# under this package so the installed CLI still has every stack template available.
_SOURCE_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SCAFFOLD_ROOT = (
    _SOURCE_ROOT
    if (_SOURCE_ROOT / "stacks").is_dir()
    else Path(__file__).resolve().parent / "resources"
)


def validate_name(name: str) -> str:
    """Validate project name: lowercase, hyphens, digits, no leading digit."""
    if not re.match(r"^[a-z][a-z0-9-]*$", name):
        raise ValueError(
            f"Invalid project name '{name}': must be lowercase letters, digits, "
            "and hyphens, starting with a letter."
        )
    return name


def validate_module_name(name: str) -> str:
    """Validate apps module name as a safe single path component."""
    try:
        return validate_name(name)
    except ValueError as e:
        raise ValueError(
            f"Invalid module name '{name}': must be lowercase letters, digits, "
            "and hyphens, starting with a letter."
        ) from e


def to_module_name(name: str) -> str:
    """Convert project name to Python module name (hyphens → underscores)."""
    return name.replace("-", "_")


SUPPORTED_STACKS = ("python", "go", "rust", "web", "blender", "threejs")
PLANNED_STACKS: tuple[str, ...] = ()
SUPPORTED_SHAPES = ("single", "apps")
WEB_UI_OPTIONS = ("plain", "tailwind", "shadcn")
WEB_DB_OPTIONS = ("d1", "drizzle-d1")


@dataclass
class Config:
    name: str
    description: str
    shape: str  # "single" | "apps"
    stack: str  # "python" | "go" | "rust" | "web"
    modules: list[str] = field(default_factory=list)
    author_name: str = ""
    author_email: str = ""
    go_module: str = ""
    install_hooks: bool = True
    keep_examples: bool = True
    web_ui: str = "plain"
    web_db: str = "d1"

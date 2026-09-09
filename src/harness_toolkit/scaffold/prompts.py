"""Interactive prompt helpers for scaffold initialization."""

from __future__ import annotations

from harness_toolkit.scaffold.config import (
    PLANNED_STACKS,
    SUPPORTED_SHAPES,
    SUPPORTED_STACKS,
    WEB_DB_OPTIONS,
    WEB_UI_OPTIONS,
    Config,
    validate_module_name,
    validate_name,
)


def gather_interactive() -> Config:
    """Prompt the user for scaffold configuration."""
    print("\n── harness-scaffold init ──\n")

    while True:
        raw = _prompt("  Project name")
        try:
            name = validate_name(raw)
            break
        except ValueError as e:
            print(f"  Error: {e}")

    description = _prompt("  Description", default=f"A {name} project")

    shape = _choose("Repo shape", list(SUPPORTED_SHAPES), default="single")
    stack = _choose("Language stack", list(SUPPORTED_STACKS), default="python")
    if stack in {"blender", "threejs"} and shape != "single":
        print(f"  The {stack} stack supports only the single-project shape.")
        shape = "single"
    if PLANNED_STACKS:
        print(f"\n  (Planned stacks not yet available: {', '.join(PLANNED_STACKS)})")

    modules: list[str] = []
    if shape == "apps":
        print("\n  Enter module names (comma-separated), e.g.: api,worker")
        while True:
            raw_modules = _prompt("  Modules", default="app")
            try:
                modules = [
                    validate_module_name(m.strip())
                    for m in raw_modules.split(",")
                    if m.strip()
                ]
                break
            except ValueError as e:
                print(f"  Error: {e}")

    author_name = _prompt("  Author name", default="")
    author_email = _prompt("  Author email", default="")

    go_module = ""
    if stack == "go":
        default_mod = f"github.com/your-org/{name}"
        go_module = _prompt("  Go module path", default=default_mod)

    web_ui = "plain"
    web_db = "d1"
    if stack == "web":
        web_ui = _choose("Web UI", list(WEB_UI_OPTIONS), default="plain")
        web_db = _choose("Web D1 access layer", list(WEB_DB_OPTIONS), default="d1")

    keep_examples = _confirm("Keep example code?", default=True)
    install_hooks = _confirm("Install pre-commit hooks?", default=True)

    return Config(
        name=name,
        description=description,
        shape=shape,
        stack=stack,
        modules=modules,
        author_name=author_name,
        author_email=author_email,
        go_module=go_module,
        install_hooks=install_hooks,
        keep_examples=keep_examples,
        web_ui=web_ui,
        web_db=web_db,
    )


def _prompt(label: str, *, default: str | None = None) -> str:
    suffix = f" [{default}]" if default is not None else ""
    value = input(f"{label}{suffix}: ").strip()
    if value:
        return value
    if default is not None:
        return default
    return ""


def _choose(label: str, choices: list[str], *, default: str) -> str:
    print(f"\n  {label}:")
    for i, choice in enumerate(choices, start=1):
        marker = " (default)" if choice == default else ""
        print(f"    {i}. {choice}{marker}")
    while True:
        raw = _prompt("  Choice", default=default)
        if raw in choices:
            return raw
        if raw.isdigit():
            idx = int(raw) - 1
            if 0 <= idx < len(choices):
                return choices[idx]
        print(f"  Choose one of: {', '.join(choices)}")


def _confirm(label: str, *, default: bool) -> bool:
    suffix = "Y/n" if default else "y/N"
    while True:
        raw = input(f"  {label} [{suffix}]: ").strip().lower()
        if not raw:
            return default
        if raw in {"y", "yes"}:
            return True
        if raw in {"n", "no"}:
            return False
        print("  Enter y or n.")

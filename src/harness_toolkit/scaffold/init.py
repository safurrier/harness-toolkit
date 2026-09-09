"""Cross-cutting init actions: docs, CI, skills, git, cleanup."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from harness_toolkit.scaffold.config import SCAFFOLD_ROOT, Config, validate_module_name
from harness_toolkit.scaffold.stacks import STACKS
from harness_toolkit.scaffold.templates import copy_tree, render_template


def build_context(
    config: Config, extra: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Build the base Jinja2 context dict from a Config."""
    ctx: dict[str, Any] = {
        "project_name": config.name,
        "project_description": config.description,
        "project_stack": config.stack,
        "project_shape": config.shape,
        "author_name": config.author_name,
        "author_email": config.author_email,
        "go_module": config.go_module,
        "module_name": config.name.replace("-", "_"),
        # Filled in by stack-specific init; safe defaults
        "stack_notes": "",
        "stack_adr_notes": "",
        "project_structure": "",
    }
    if extra:
        ctx.update(extra)
    return ctx


def generate_docs(root: Path, context: dict[str, Any]) -> None:
    """Generate README, AGENTS.md + CLAUDE.md symlink, docs/, CI template."""
    tmpl_dir = SCAFFOLD_ROOT / "templates"

    # Remove scaffold's own docs/ (MkDocs site) before generating project docs
    scaffold_docs = root / "docs"
    if scaffold_docs.is_dir():
        shutil.rmtree(scaffold_docs)

    # README.md
    readme_tmpl = tmpl_dir / "README.md.tmpl"
    if readme_tmpl.exists():
        _write(readme_tmpl, root / "README.md", context)

    # SPEC.md
    spec_tmpl = tmpl_dir / "SPEC.md.tmpl"
    if spec_tmpl.exists():
        _write(spec_tmpl, root / "SPEC.md", context)

    # AGENTS.md + CLAUDE.md → AGENTS.md symlink
    agents_tmpl = tmpl_dir / "AGENTS.md.tmpl"
    if agents_tmpl.exists():
        _write(agents_tmpl, root / "AGENTS.md", context)
        _make_symlink(root / "CLAUDE.md", "AGENTS.md", fallback_src=root / "AGENTS.md")

    # docs/ (intent-structured tree, review rubrics, decision ledger, ADR seed)
    docs_src = tmpl_dir / "docs"
    if docs_src.exists():
        scaffold_docs.mkdir(parents=True, exist_ok=True)
        copy_tree(docs_src, scaffold_docs, context)

    # .agent/skills/ (full tree, includes example-skill/)
    # Remove scaffold's own skills before copying template skills
    skills_dst = root / ".agent" / "skills"
    if skills_dst.is_dir():
        shutil.rmtree(skills_dst)
    skills_src = tmpl_dir / ".agent" / "skills"
    if skills_src.exists():
        skills_dst.mkdir(parents=True, exist_ok=True)
        copy_tree(skills_src, skills_dst, context)

    # .ai/plans/ (AGENTS.md routing index, templates, example)
    plans_dst = root / ".ai" / "plans"
    if plans_dst.is_dir():
        shutil.rmtree(plans_dst)
    plans_src = tmpl_dir / ".ai" / "plans"
    if plans_src.exists():
        plans_dst.mkdir(parents=True, exist_ok=True)
        copy_tree(plans_src, plans_dst, context)

    # .claude/skills → ../.agent/skills symlink
    claude_dir = root / ".claude"
    claude_dir.mkdir(exist_ok=True)
    _make_symlink(
        claude_dir / "skills",
        Path("..") / ".agent" / "skills",
        fallback_src=root / ".agent" / "skills",
        is_dir_fallback=True,
    )

    # .github/workflows/ci.yml
    ci_tmpl = tmpl_dir / ".github" / "workflows" / "ci.yml.tmpl"
    if ci_tmpl.exists():
        _write(ci_tmpl, root / ".github" / "workflows" / "ci.yml", context)


def rewrite_mise_toml(root: Path, config: Config) -> None:
    """Rewrite .mise.toml with project-specific configuration."""
    stack = STACKS[config.stack]
    tools_section = f"[tools]\n{stack.tools_toml()}"

    content = f"""#:schema https://mise.jdx.dev/schema/mise.json

# ─────────────────────────────────────────────
# {config.name} — mise configuration
# ─────────────────────────────────────────────

{tools_section}
[env]
MISE_PROJECT_ROOT = "{{{{config_root}}}}"
SCAFFOLD_PROJECT_NAME  = "{config.name}"
SCAFFOLD_PROJECT_SHAPE = "{config.shape}"
SCAFFOLD_PROJECT_STACK = "{config.stack}"
"""
    (root / ".mise.toml").write_text(content)


def generate_workspace_toml(
    root: Path, config: Config, context: dict[str, Any]
) -> None:
    """Generate workspace.toml for apps shape."""
    modules_data = {
        name: {"path": f"apps/{name}", "kind": config.stack, "role": "app"}
        for name in config.modules
    }
    tmpl = SCAFFOLD_ROOT / "templates" / "apps" / "workspace.toml.tmpl"
    if tmpl.exists():
        _write(tmpl, root / "workspace.toml", {**context, "modules": modules_data})


def cleanup_scaffold(root: Path, config: Config) -> None:
    """Remove scaffold-only artifacts after init."""
    to_remove = [
        root / "stacks",
        root / "templates",
        root / "src" / "harness_toolkit",  # scaffold CLI package (not whole src/)
        root / "mkdocs.yml",  # scaffold's MkDocs config
        # Harness Toolkit's own docs deploy workflow requires mkdocs.yml and GitHub
        # Pages configuration. Generated repos get docs/ but not MkDocs publishing
        # by default, so do not accidentally retain the scaffold repo workflow.
        root / ".github" / "workflows" / "docs.yml",
        root / "scripts" / "init_project.py",  # legacy, may not exist
    ]

    stack_owns_root_tests = config.shape == "single" and config.stack in {
        "python",
        "web",
        "blender",
        "threejs",
    }
    if not stack_owns_root_tests:
        to_remove.append(root / "tests")
    if config.stack not in {"python", "blender"} or config.shape == "apps":
        # The root lock belongs to the scaffold project whenever its metadata is
        # removed. Stack-owned locks (including Blender's) remain intact.
        to_remove.extend([root / "pyproject.toml", root / "uv.lock"])

    for path in to_remove:
        if path.is_dir():
            shutil.rmtree(path)
        elif path.is_file():
            path.unlink(missing_ok=True)

    # Remove src/ only if empty (Rust init_single writes src/main.rs there)
    src_dir = root / "src"
    if src_dir.is_dir() and not any(src_dir.iterdir()):
        src_dir.rmdir()

    scripts_dir = root / "scripts"
    if scripts_dir.exists() and not any(scripts_dir.iterdir()):
        scripts_dir.rmdir()


def git_init(root: Path, config: Config) -> None:
    """Initialize git and make the first commit."""
    git_dir = root / ".git"
    if git_dir.exists():
        shutil.rmtree(git_dir)

    env = {
        **os.environ,
        "GIT_AUTHOR_NAME": config.author_name or "harness-scaffold",
        "GIT_AUTHOR_EMAIL": config.author_email or "init@harness-scaffold",
        "GIT_COMMITTER_NAME": config.author_name or "harness-scaffold",
        "GIT_COMMITTER_EMAIL": config.author_email or "init@harness-scaffold",
    }

    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "add", "-A"], cwd=root, check=True, capture_output=True)
    subprocess.run(
        [
            "git",
            "commit",
            "--no-verify",
            "-m",
            f"feat: initialize {config.name} project",
        ],
        cwd=root,
        check=True,
        capture_output=True,
        env=env,
    )


def install_pre_commit(root: Path) -> None:
    """Install pre-commit hooks if available."""
    if shutil.which("pre-commit") and (root / ".git").exists():
        subprocess.run(
            ["pre-commit", "install"], cwd=root, check=True, capture_output=True
        )


# ── private helpers ───────────────────────────────────────────────────────────


def _write(src: Path, dst: Path, context: dict[str, Any]) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(render_template(src, context))


def _make_symlink(
    link: Path,
    target: Path | str,
    *,
    fallback_src: Path,
    is_dir_fallback: bool = False,
) -> None:
    """Create *link* → *target* symlink, falling back to copy on Windows."""
    if link.exists() or link.is_symlink():
        if link.is_symlink() or link.is_file():
            link.unlink()
        else:
            shutil.rmtree(link)
    try:
        link.symlink_to(target)
    except OSError:
        if is_dir_fallback:
            shutil.copytree(fallback_src, link)
        else:
            shutil.copy2(fallback_src, link)


def run_init(root: Path, config: Config) -> None:
    """Execute the full scaffold-to-project transformation."""
    from harness_toolkit.scaffold.stacks import STACKS

    stack = STACKS[config.stack]

    print(f"\n── Initializing {config.name} ({config.shape}/{config.stack}) ──\n")

    # 1. Stack-specific file layout
    print("==> Applying stack templates")
    if config.shape == "single":
        extra = stack.init_single(root, config)
    else:
        extra = _init_apps(root, config, stack)

    # 2. Build context and generate docs/CI/skills
    context = build_context(config, extra)
    print("==> Generating docs, CI, skills")
    generate_docs(root, context)

    # 3. Rewrite .mise.toml
    rewrite_mise_toml(root, config)

    # 4. workspace.toml (apps shape)
    if config.shape == "apps":
        generate_workspace_toml(root, config, context)

    # 5. Remove examples if requested
    if not config.keep_examples:
        print("==> Removing example code")
        if config.shape == "single":
            stack.remove_examples(root, config)
        else:
            for mod_name in config.modules:
                stack.remove_module_examples(root / "apps" / mod_name)

    # 6. Clean up scaffold artifacts
    print("==> Cleaning up scaffold artifacts")
    cleanup_scaffold(root, config)

    # 7. Git init
    git_init(root, config)
    print("  ✓ Git repository initialized")

    # 8. Pre-commit hooks
    if config.install_hooks:
        install_pre_commit(root)
        print("  ✓ Pre-commit hooks installed")

    print(f"\n── {config.name} is ready! ──")
    print("\n  Next steps:")
    print("    mise run setup    # install dependencies")
    print("    mise run check    # verify everything works")
    print("    mise run dev      # start developing")
    print()


def _init_apps(root: Path, config: Config, stack: Any) -> dict[str, str]:
    """Initialize apps workspace layout."""
    modules = config.modules or ["app"]
    extra: dict[str, str] = {}

    apps_root = (root / "apps").resolve()
    for raw_mod_name in modules:
        mod_name = validate_module_name(raw_mod_name)
        mod_dir = root / "apps" / mod_name
        if not mod_dir.resolve().is_relative_to(apps_root):
            raise ValueError(f"Invalid module path escapes apps directory: {mod_name}")
        mod_dir.mkdir(parents=True, exist_ok=True)
        mod_extra = stack.init_module(mod_dir, config, mod_name)
        extra.update(mod_extra)

    # packages/ placeholder
    (root / "packages").mkdir(exist_ok=True)
    (root / "packages" / ".gitkeep").touch()

    # .gitignore for apps workspace
    gitignore_tmpl = SCAFFOLD_ROOT / "templates" / "apps" / ".gitignore.tmpl"
    if gitignore_tmpl.exists():
        _write(gitignore_tmpl, root / ".gitignore", {})

    # Generate project_structure
    mod_tree = "\n".join(f"│   └── {m}/" for m in modules)
    extra["project_structure"] = f"""\
```
{config.name}/
├── apps/
{mod_tree}
├── packages/               # Shared libraries
├── workspace.toml          # Module registry
├── .mise.toml              # Task runner config
└── README.md
```"""

    return extra

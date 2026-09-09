"""Web stack implementation."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from harness_toolkit.scaffold.config import SCAFFOLD_ROOT, Config
from harness_toolkit.scaffold.templates import copy_tree, render_template


class WebStack:
    def tools_toml(self) -> str:
        return 'python = "3.12"\nuv = "latest"\nnode = "22"\nnpm = "11.6.2"\n'

    def adr_notes(self) -> str:
        return """\
The Web stack uses:
- **Vite + React** for the browser app
- **TypeScript** for static checking
- **Cloudflare Workers + Static Assets** for hosting and API routes
- **D1 migrations** for relational app state when persistence is enabled
- **Vitest**, **ESLint**, and **Prettier** for validation"""

    def stack_notes(self) -> str:
        return """\
- Formatter: prettier
- Linter: eslint
- Type checker: tsc --noEmit
- Tests: vitest
- Build: vite build
- Deploy dry-run: wrangler deploy --dry-run"""

    def init_single(self, root: Path, config: Config) -> dict[str, str]:
        stack_dir = SCAFFOLD_ROOT / "stacks" / "web"
        context = _build_context(config, config.name)

        tests_dir = root / "tests"
        if tests_dir.exists():
            shutil.rmtree(tests_dir)
        copy_tree(stack_dir / "project", root, context)
        _apply_web_options(root, config)

        gitignore = SCAFFOLD_ROOT / "templates" / "single" / ".gitignore.web.tmpl"
        if gitignore.exists():
            _write(gitignore, root / ".gitignore", context)

        return {
            "project_structure": _single_structure(config.name),
            "stack_notes": self.stack_notes(),
            "stack_adr_notes": self.adr_notes(),
        }

    def init_module(
        self, mod_dir: Path, config: Config, mod_name: str
    ) -> dict[str, str]:
        stack_dir = SCAFFOLD_ROOT / "stacks" / "web"
        context = _build_context(config, mod_name)

        copy_tree(stack_dir / "project", mod_dir, context)
        _apply_web_options(mod_dir, config)

        return {
            "stack_notes": self.stack_notes(),
            "stack_adr_notes": self.adr_notes(),
        }

    def remove_examples(self, root: Path, config: Config) -> None:
        for path in [
            root / "src" / "app" / "ExamplePanel.tsx",
            root / "tests" / "app.test.ts",
        ]:
            if path.exists():
                path.unlink()
        _write_minimal_app(
            root / "src" / "app" / "App.tsx", config.name, config.description
        )

    def remove_module_examples(self, mod_dir: Path) -> None:
        for rel_path in [
            Path("src") / "app" / "ExamplePanel.tsx",
            Path("tests") / "app.test.ts",
        ]:
            path = mod_dir / rel_path
            if path.exists():
                path.unlink()
        _write_minimal_app(mod_dir / "src" / "app" / "App.tsx", mod_dir.name, "")


def _build_context(config: Config, package_name: str) -> dict[str, Any]:
    return {
        "project_name": package_name,
        "project_description": config.description,
        "project_description_template_literal": _tsx_template_literal(
            config.description
        ),
        "project_stack": config.stack,
        "author_name": config.author_name,
        "author_email": config.author_email,
        "module_name": package_name.replace("-", "_"),
        "web_package_name": package_name,
        "web_ui": config.web_ui,
        "web_db": config.web_db,
        "web_ui_tailwind": config.web_ui in {"tailwind", "shadcn"},
        "web_ui_shadcn": config.web_ui == "shadcn",
        "web_db_drizzle": config.web_db == "drizzle-d1",
        "web_format_extra_files": " components.json"
        if config.web_ui == "shadcn"
        else "",
        "web_dependencies_json_entries": _package_entries(_web_dependencies(config)),
        "web_dev_dependencies_json_entries": _package_entries(
            _web_dev_dependencies(config)
        ),
    }


def _web_dependencies(config: Config) -> dict[str, str]:
    dependencies = {
        "react": "^19.0.0",
        "react-dom": "^19.0.0",
    }
    if config.web_db == "drizzle-d1":
        dependencies = {"drizzle-orm": "^0.45.2", **dependencies}
    if config.web_ui == "shadcn":
        dependencies.update(
            {
                "class-variance-authority": "^0.7.1",
                "clsx": "^2.1.1",
                "lucide-react": "^1.17.0",
                "tailwind-merge": "^3.6.0",
            }
        )
    return dependencies


def _web_dev_dependencies(config: Config) -> dict[str, str]:
    dependencies = {
        "@cloudflare/workers-types": "5.20260908.1",
        "@eslint/js": "^9.17.0",
        "@vitejs/plugin-react": "^6.0.2",
        "@types/node": "^22.10.2",
        "@types/react": "^19.0.2",
        "@types/react-dom": "^19.0.2",
        "eslint": "^9.17.0",
        "prettier": "^3.4.2",
        "typescript": "^5.7.3",
        "typescript-eslint": "^8.19.0",
        "vite": "^8.0.16",
        "@vitest/browser-playwright": "4.1.11",
        "vitest": "4.1.11",
        "wrangler": "4.130.0",
    }
    if config.web_ui in {"tailwind", "shadcn"}:
        dependencies = {
            **dependencies,
            "@tailwindcss/vite": "^4.3.0",
            "tailwindcss": "^4.3.0",
        }
    return dict(sorted(dependencies.items()))


def _package_entries(dependencies: dict[str, str]) -> str:
    lines = [
        f"    {json.dumps(name)}: {json.dumps(version)}"
        for name, version in dependencies.items()
    ]
    return ",\n".join(lines)


def _apply_web_options(root: Path, config: Config) -> None:
    if config.web_ui == "shadcn":
        _write_shadcn_files(root)
    if config.web_db == "drizzle-d1":
        _write_drizzle_schema(root)


def _write_shadcn_files(root: Path) -> None:
    _write_text(
        root / "components.json",
        """\
{
  "$schema": "https://ui.shadcn.com/schema.json",
  "style": "new-york",
  "rsc": false,
  "tsx": true,
  "tailwind": {
    "css": "src/styles.css",
    "baseColor": "slate",
    "cssVariables": true
  },
  "aliases": {
    "components": "@/components",
    "utils": "@/lib/utils",
    "ui": "@/components/ui",
    "lib": "@/lib"
  }
}
""",
    )
    _write_text(
        root / "src" / "lib" / "utils.ts",
        """\
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
""",
    )
    _write_text(
        root / "src" / "components" / "ui" / "button.tsx",
        """\
import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-400 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-slate-900 text-slate-50 hover:bg-slate-800",
        secondary: "bg-slate-100 text-slate-900 hover:bg-slate-200",
        outline: "border border-slate-300 bg-white hover:bg-slate-50",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 rounded-md px-3",
        lg: "h-11 rounded-md px-8",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
);

export interface ButtonProps
  extends
    React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

export function Button({ className, variant, size, ...props }: ButtonProps) {
  return (
    <button
      className={cn(buttonVariants({ variant, size }), className)}
      {...props}
    />
  );
}
""",
    )


def _write_drizzle_schema(root: Path) -> None:
    _write_text(
        root / "worker" / "db" / "schema.ts",
        """\
import { sqliteTable, text } from "drizzle-orm/sqlite-core";

export const savedRuns = sqliteTable("saved_runs", {
  id: text("id").primaryKey(),
  ownerId: text("owner_id").notNull(),
  title: text("title").notNull(),
  lineupJson: text("lineup_json").notNull(),
  resultJson: text("result_json").notNull(),
  createdAt: text("created_at").notNull(),
});
""",
    )


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def _write(src: Path, dst: Path, context: dict[str, Any]) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(render_template(src, context))


def _tsx_template_literal(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")
    return f"`{escaped}`"


def _write_minimal_app(path: Path, project_name: str, description: str) -> None:
    path.write_text(
        f"""\
export function App() {{
  return (
    <main className="app-shell">
      <section className="hero">
        <p className="eyebrow">Harness web stack</p>
        <h1>{project_name}</h1>
        <p className="summary">{{{_tsx_template_literal(description or "Ready for implementation.")}}}</p>
      </section>
    </main>
  );
}}
"""
    )


def _single_structure(project_name: str) -> str:
    return f"""\
```
{project_name}/
├── src/                    # React browser app
├── worker/                 # Cloudflare Worker API routes
├── migrations/             # D1 migrations
├── tests/                  # Vitest coverage
├── public/                 # Static assets and seed data
├── .mise.toml              # Task runner config
├── package.json            # Web tooling scripts
├── wrangler.jsonc          # Cloudflare Worker config
└── README.md
```"""

"""Verify docs frontmatter and structure for the scaffold itself.

These tests run on the scaffold's own docs/ directory (before any init).
Fast — no subprocess, just file-system assertions.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from tests._docs_helpers import (
    ARCHITECTURE_REQUIRED_SECTIONS,
    SPEC_REQUIRED_SECTIONS,
    find_doc_files,
    find_section,
    has_frontmatter,
    parse_frontmatter,
    parse_sections,
    validate_frontmatter,
)
from tests._support import SCAFFOLD_ROOT

pytestmark = pytest.mark.contract

DOCS_DIR = SCAFFOLD_ROOT / "docs"
TEMPLATES_DIR = SCAFFOLD_ROOT / "templates"
STACK_RUBRIC = DOCS_DIR / "reference" / "stacks" / "acceptance-rubric.md"

# All docs/*.md files that MUST have frontmatter (excludes docs/AGENTS.md)
DOCS_WITH_FRONTMATTER = find_doc_files(DOCS_DIR)

# Files that must NOT have frontmatter
NO_FRONTMATTER_FILES = [
    SCAFFOLD_ROOT / "AGENTS.md",
    DOCS_DIR / "AGENTS.md",
]


# ── Frontmatter presence ──────────────────────────────────────────────────


@pytest.mark.parametrize(
    "doc",
    DOCS_WITH_FRONTMATTER,
    ids=lambda p: str(p.relative_to(SCAFFOLD_ROOT)),
)
def test_doc_has_frontmatter(doc: Path) -> None:
    """Every docs/*.md file (except AGENTS.md) must have YAML frontmatter."""
    assert has_frontmatter(doc), (
        f"{doc.relative_to(SCAFFOLD_ROOT)} is missing YAML frontmatter (---)"
    )


@pytest.mark.parametrize(
    "path",
    [p for p in NO_FRONTMATTER_FILES if p.exists()],
    ids=lambda p: str(p.relative_to(SCAFFOLD_ROOT)),
)
def test_agents_md_has_no_frontmatter(path: Path) -> None:
    """AGENTS.md files must NOT have frontmatter — only docs/ files get it."""
    assert not has_frontmatter(path), (
        f"{path.relative_to(SCAFFOLD_ROOT)} should NOT have frontmatter"
    )


# ── Frontmatter schema validation ─────────────────────────────────────────


@pytest.mark.parametrize(
    "doc",
    DOCS_WITH_FRONTMATTER,
    ids=lambda p: str(p.relative_to(SCAFFOLD_ROOT)),
)
def test_doc_frontmatter_is_valid(doc: Path) -> None:
    """Frontmatter must have id, title, description, and non-empty index."""
    fm = parse_frontmatter(doc)
    if fm is None:
        pytest.skip("no frontmatter (covered by test_doc_has_frontmatter)")
    errors = validate_frontmatter(fm)
    assert not errors, (
        f"{doc.relative_to(SCAFFOLD_ROOT)} frontmatter errors: {'; '.join(errors)}"
    )


# ── Uniqueness ────────────────────────────────────────────────────────────


def test_doc_ids_are_unique() -> None:
    """All frontmatter ids across docs/ must be unique."""
    ids: dict[str, Path] = {}
    for doc in DOCS_WITH_FRONTMATTER:
        fm = parse_frontmatter(doc)
        if fm is None or not fm.id:
            continue
        if fm.id in ids:
            pytest.fail(
                f"Duplicate id '{fm.id}' in "
                f"{doc.relative_to(SCAFFOLD_ROOT)} and "
                f"{ids[fm.id].relative_to(SCAFFOLD_ROOT)}"
            )
        ids[fm.id] = doc


# ── Index entries have keywords ───────────────────────────────────────────


@pytest.mark.parametrize(
    "doc",
    DOCS_WITH_FRONTMATTER,
    ids=lambda p: str(p.relative_to(SCAFFOLD_ROOT)),
)
def test_doc_index_entries_have_keywords(doc: Path) -> None:
    """Every index entry must have at least one keyword."""
    fm = parse_frontmatter(doc)
    if fm is None:
        pytest.skip("no frontmatter")
    for entry in fm.index:
        keywords = entry.get("keywords", [])
        assert keywords, (
            f"{doc.relative_to(SCAFFOLD_ROOT)}: "
            f"index entry '{entry.get('id', '?')}' has no keywords"
        )


# ── mkdocs.yml consistency ────────────────────────────────────────────────


def test_mkdocs_nav_entries_exist() -> None:
    """Every .md path listed in mkdocs.yml nav must exist on disk."""
    mkdocs_yml = SCAFFOLD_ROOT / "mkdocs.yml"
    if not mkdocs_yml.exists():
        pytest.skip("mkdocs.yml not found")
    content = mkdocs_yml.read_text()
    for m in re.finditer(r":\s+(\S+\.md)\s*$", content, re.MULTILINE):
        md_path = DOCS_DIR / m.group(1)
        assert md_path.exists(), (
            f"mkdocs.yml references {m.group(1)} but {md_path} does not exist"
        )


# ── Stack acceptance rubric ──────────────────────────────────────────────


def test_stack_acceptance_rubric_exists() -> None:
    assert STACK_RUBRIC.exists(), (
        "docs/reference/stacks/acceptance-rubric.md is missing"
    )


def test_stack_acceptance_rubric_covers_required_contract() -> None:
    content = " ".join(STACK_RUBRIC.read_text().lower().split())
    required_terms = [
        "single-project",
        "apps-shape",
        "setup",
        "fmt",
        "lint",
        "typecheck",
        "test",
        "build",
        "generated-project smoke matrix",
        "release build",
        "docker",
        "reviewer checklist",
    ]

    for term in required_terms:
        assert term in content, f"Stack rubric missing required term: {term}"


def test_development_guide_links_stack_rubric() -> None:
    content = (DOCS_DIR / "how-to" / "development.md").read_text()
    assert "../reference/stacks/acceptance-rubric.md" in content


def test_task_contract_docs_verification_routes() -> None:
    content = (DOCS_DIR / "reference" / "task-contract.md").read_text()
    assert "verification.toml" in content
    assert "verify-routes" in content
    assert "Surface, Run, Drive, Observe, Isolate" in content


# ── Architecture.md template structure ───────────────────────────────────

ARCH_TEMPLATE = TEMPLATES_DIR / "docs" / "explanation" / "architecture.md.tmpl"


@pytest.mark.parametrize("section_name", ARCHITECTURE_REQUIRED_SECTIONS)
def test_architecture_template_has_required_section(section_name: str) -> None:
    """architecture.md template must contain all RFC-required H2 sections."""
    assert ARCH_TEMPLATE.exists(), "architecture.md.tmpl not found"
    sections = parse_sections(ARCH_TEMPLATE)
    match = find_section(sections, section_name, level=2)
    assert match is not None, (
        f"architecture.md.tmpl missing required section matching '{section_name}'"
    )


def test_architecture_template_invariants_nonempty() -> None:
    """Invariants section must have content (not just heading stubs)."""
    sections = parse_sections(ARCH_TEMPLATE)
    inv = find_section(sections, "Invariants", level=2)
    assert inv is not None
    # Should have subsections or content beyond just HTML comments
    assert len(inv.content) > 50, "Invariants section appears empty or stub-only"


def test_architecture_template_has_truth_hierarchy() -> None:
    """Decisions section must define truth hierarchy."""
    sections = parse_sections(ARCH_TEMPLATE)
    dec = find_section(sections, "Decisions", level=2)
    assert dec is not None
    assert "truth hierarchy" in dec.content.lower(), (
        "Decisions section missing truth hierarchy definition"
    )


def test_architecture_template_has_decisions_index_table() -> None:
    """Decisions section must contain a markdown table linking to ADRs."""
    sections = parse_sections(ARCH_TEMPLATE)
    dec = find_section(sections, "Decisions", level=2)
    assert dec is not None
    assert "|" in dec.content and "ADR" in dec.content, (
        "Decisions section missing ADR index table"
    )


# ── ADR template structure ───────────────────────────────────────────────

ADR_TEMPLATE = (
    TEMPLATES_DIR / "docs" / "explanation" / "decisions" / "0001-stack-choice.md.tmpl"
)

LEDGER_TEMPLATE = TEMPLATES_DIR / "docs" / "explanation" / "decision-ledger.md.tmpl"


def test_adr_template_has_status_field() -> None:
    """ADR template must include a Status field."""
    content = ADR_TEMPLATE.read_text()
    assert "**Status**:" in content, "ADR template missing **Status** field"


def test_adr_template_has_generated_from_field() -> None:
    """ADR template must include a Generated from field for traceability."""
    content = ADR_TEMPLATE.read_text()
    assert "**Generated from**:" in content, (
        "ADR template missing **Generated from** field"
    )


def test_adr_template_has_required_sections() -> None:
    """ADR template must have Context, Decision, and Consequences sections."""
    sections = parse_sections(ADR_TEMPLATE)
    for required in ["Context", "Decision", "Consequences"]:
        match = find_section(sections, required, level=2)
        assert match is not None, (
            f"ADR template missing required section '## {required}'"
        )


def test_decision_ledger_template_exists() -> None:
    assert LEDGER_TEMPLATE.exists(), "decision-ledger.md.tmpl not found"


def test_decision_ledger_template_mentions_append_only() -> None:
    content = LEDGER_TEMPLATE.read_text().lower()
    assert "append-only" in content, (
        "decision ledger template must state append-only behavior"
    )


# ── SPEC.md template structure ───────────────────────────────────────────

SPEC_TEMPLATE = TEMPLATES_DIR / "SPEC.md.tmpl"


def test_spec_template_exists() -> None:
    """SPEC.md template must exist."""
    assert SPEC_TEMPLATE.exists(), "templates/SPEC.md.tmpl not found"


def test_spec_template_has_frontmatter() -> None:
    """SPEC.md template must have YAML frontmatter."""
    assert has_frontmatter(SPEC_TEMPLATE), "SPEC.md.tmpl missing frontmatter"


@pytest.mark.parametrize("section_name", SPEC_REQUIRED_SECTIONS)
def test_spec_template_has_required_section(section_name: str) -> None:
    """SPEC.md template must contain all required H2 sections."""
    sections = parse_sections(SPEC_TEMPLATE)
    match = find_section(sections, section_name, level=2)
    assert match is not None, (
        f"SPEC.md.tmpl missing required section matching '{section_name}'"
    )


def test_spec_template_has_must_requirements() -> None:
    """SPEC.md template Requirements section must have a MUST subsection."""
    sections = parse_sections(SPEC_TEMPLATE)
    req = find_section(sections, "Requirements", level=2)
    assert req is not None
    assert find_section(sections, "MUST", level=3) is not None, (
        "SPEC.md Requirements section missing ### MUST subsection"
    )


def test_spec_template_references_check_command() -> None:
    """SPEC.md Acceptance section should reference mise run check."""
    sections = parse_sections(SPEC_TEMPLATE)
    acc = find_section(sections, "Acceptance", level=2)
    assert acc is not None
    assert "mise run check" in acc.content, (
        "SPEC.md Acceptance section should reference 'mise run check'"
    )

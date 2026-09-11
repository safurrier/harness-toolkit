---
id: agent-scaffold-adr-0002
title: ADR 0002 — Plan-Based Workflow
description: >
  Adds structured plan directories with META.yaml, TODO, learning log,
  and validation log as the standard way to start and track units of work.
index:
  - id: decision
    keywords: [plan, workflow, meta, todo, learning-log, validation, mise-task]
  - id: consequences
    keywords: [pre-push, plan-sync, templates, example]
---

# ADR 0002: Plan-Based Workflow

**Status**: Accepted
**Date**: 2026-03-08
**Deciders**: Alex Furrier
**Generated from**: agent-session

---

## Context

The spec-driven decision loop (ADR 0001) established pre-push skills for keeping
docs current, but had no convention for **how to start work**. Agents picking up
a task would jump straight to coding without scoping, and there was no structured
place to capture problems, adaptations, or validation evidence during development.

The user's personal AGENTS.md had a plan convention (the now-retired `.ai/plans/`
directory with SPEC, TODO, IMPLEMENTATION, LEARNING_LOG) but it wasn't part of
harness-scaffold's generated repos.

## Decision

Add a plan-based workflow to harness-scaffold:

- **`mise run plan -- <slug>`** creates `.ai/plans/YYYY-MM-DD-HHmm-<slug>/` with templates
- **4 required files**: META.yaml (machine-readable metadata), TODO.md (task list),
  LEARNING_LOG.md (dev diary), VALIDATION.md (verification log)
- **2 optional files**: SPEC.md (requirements), IMPLEMENTATION.md (approach)
- **Example plan** in the historical scaffold plan-template directory, now
  retired, showing the full lifecycle for agent reference
- **`/plan-sync` skill** validates plan artifacts are current before pushing
- **META.yaml** is structured YAML with required fields (slug, created, status)
  for future tooling (Groundskeeper, dashboards)
- **LEARNING_LOG as dev diary**: append timestamped entries during work (problems,
  adaptations, feedback), not just retrospective at completion

Only TODO.md is truly required to start — the overhead is one command and editing
a task list. SPEC.md and IMPLEMENTATION.md are for heavier work.

## Consequences

**Positive:**

- Every unit of work has a structured home with machine-readable metadata
- Learning log captures problems and feedback as they happen, not reconstructed later
- Validation log provides audit trail of how changes were verified
- Example plan teaches agents the convention by showing, not just telling
- `mise run plan` is zero-overhead — one command, templates auto-filled

**Negative / Trade-offs:**

- More files in `.ai/plans/` over time (mitigated: old plans are historical, not active)
- `plan-sync` adds one more pre-push step (mitigated: fast no-op when nothing changed)
- META.yaml is a new file format to validate (mitigated: simple YAML, stdlib parser)

## Alternatives Considered

| Alternative | Reason not chosen |
|---|---|
| YAML block in TODO.md instead of META.yaml | Harder to parse mechanically, mixes content and metadata |
| No required files (all optional) | Too loose — no guarantee plans have minimum structure |
| Auto-create branch from slug | Branch naming is semantic, needs agent/human judgment |
| Groundskeeper orchestration for plan lifecycle | Over-engineered for v1 — convention + contract tests sufficient |

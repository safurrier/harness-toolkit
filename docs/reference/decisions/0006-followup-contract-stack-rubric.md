---
id: agent-scaffold-adr-0006
title: ADR 0006 — Plan Contract Modules and Stack Rubric
description: >
  Moves the slice workflow implementation into its skill-local CLI, and records
  a stack acceptance rubric for future language stacks.
index:
  - id: decision
    keywords: [slice-workflow, skill-cli, stack-rubric, acceptance]
  - id: consequences
    keywords: [compatibility, future-stacks, generated-repos]
---

# ADR 0006: Slice Workflow Skill CLI and Stack Rubric

**Status**: Accepted
**Date**: 2026-04-29
**Deciders**: Alex Furrier
**Generated from**: GitHub issues #6 and #7
**Plan**: `.ai/plans/2026-04-29-154802-followup-contract-stack-rubric/`

---

## Context

The deterministic slice work left two follow-up concerns.

First, the slice workflow had grown into several repo-local scripts. The
planning, prompt rendering, and handoff checks were still exposed through stable
`mise` tasks, but their implementation lived partly in `scripts/`. That split
made the workflow feel less like a portable skill and more like scaffold-only
plumbing.

Second, the Rust stack made the project's implicit stack quality bar visible.
Python, Go, and Rust all cover a broad happy path, but the project did not yet
state what future stacks must provide before they count as supported.

## Decision

The `mise` tasks remained the stable agent-facing interface. Their implementation
then delegated to the skill-local slice-workflow CLI in scaffold source and
generated repositories. Those CLI paths were retired with the generated
slice-plan workflow; this is historical architecture, not a live path reference.

The CLI uses a tiny uv project and the `slice_workflow_cli` package:

- `plan.py` creates plan directories from templates.
- `workflow.py` renders planner, implementer, and reviewer prompts.
- `checks.py` runs the plan/spec/evidence/review/sync contract checks.
- The contract package contains plan, git, markdown, artifact, and docs helpers.

The project now also has `docs/reference/stacks/acceptance-rubric.md`, which defines the
required future-stack bar and reviewer checklist.

## Consequences

**Positive:**

- Workflow code moves with the `slice-workflow` skill into generated repos.
- The deterministic command surface remains `mise run ...`.
- Future plan-contract changes should land in smaller files with clearer names.
- Future stack PRs have an explicit review checklist instead of relying on the
  Rust stack as an implicit example.

**Negative / Trade-offs:**

- The skill now carries a small CLI project and lockfile.
- The task wrappers duplicate a small launcher to keep `.mise/tasks/*` directly
  executable and provider-neutral.

## Alternatives Considered

| Alternative | Reason not chosen |
|---|---|
| Keep one `plan_contract.py` file | Too much unrelated logic in one review unit |
| Keep repo-local modules under `scripts/` | It preserves old imports but conflicts with the skill-local mini CLI pattern |
| Make the new CLI user-facing | More disruption than needed; task names are already the stable interface |
| Add a third-party YAML or CLI library | Generated repos should keep contract checks dependency-light |

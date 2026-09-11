---
id: agent-skills-index
title: Skills
description: >
  Index of optional workflow helpers for this repository. Each skill encodes a
  repeatable procedure that agents or humans can load when it fits the task.
index:
  - id: adding-a-skill
    keywords: [add-skill, skill-md, references, scripts, structure]
  - id: verification
    keywords: [verification, routes, user-journeys, browser, runtime]
  - id: policy
    keywords: [policy, optional, preference, ci-enforcement, canonical-truth]
---

# Skills

Vendored workflow helpers for agents and humans working in this repository.

Skills help apply repository-owned commands and durable docs; they are not the
canonical source of truth. `mise run check` is the fast quality gate and
`mise run verify` is the heavier product-verification entry point.

Each skill follows this structure:

```
.agent/skills/<skill-name>/
├── SKILL.md          # When to use this skill and the workflow it encodes
├── references/       # Reference materials: context, docs, examples
└── scripts/          # Automation scripts used by the skill
```

## Product Verification

Use `create-project-verification` when a feature or caller journey lacks a
trustworthy proof route. Use `maintain-project-verification` when a changed
public surface, dependency, readiness step, observation, or cleanup rule may
make an existing route stale. Routes belong in `scripts/verify/`, map affected
paths in `.harness/verification.toml`, and must observe the claimed behavior or
side effect. A green build, test count, screenshot, or exit code alone is not
proof of a user journey.

Run only affected routes while iterating:

```bash
scripts/verify-routes --path src/records/api.py
```

No selector runs every required automated route. Manual or credentialed checks
remain explicit operator obligations rather than automated passes.

## Adding a Skill

A starter template is in `example-skill/SKILL.md`. Copy it:

```bash
cp -r .agent/skills/example-skill/ .agent/skills/<your-skill-name>/
```

Then edit `SKILL.md` to describe:

- When to load this skill (activation signals)
- The opinionated workflow it encodes
- Any references or scripts alongside it

Reference the skill from `AGENTS.md` if it applies broadly.

## Policy

Skills are workflow helpers. System truth stays in `docs/`, source, and native
commands; repeatable procedures can live in a skill when a repo-owned command
is the deterministic interface.

- If a workflow is universally agreed and objective → encode it in `mise` tasks
- If a workflow is repeatable but harness-specific → vendor it here as a skill
- If a standard becomes durable repo knowledge → move it into `docs/`

## Bundled Skills

- `context-engineering` — keeps docs routing and repository context current
- `harness-kit-profile-authoring` — mines validation contracts and proposes custom `hk` profiles
- `hk-config-authoring` — routes profile and system-map authoring work
- `hk-system-map-author` — maintains component and invariant context maps
- `create-project-verification` — creates an executable proof route for a missing user or caller journey
- `maintain-project-verification` — keeps affected proof routes truthful after changes

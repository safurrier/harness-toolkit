---
id: harness-toolkit-spec
title: harness-toolkit specification
description: >
  Current correctness envelope for scaffolded repositories and the optional
  Harness Kit lifecycle tool.
index:
  - id: requirements
    keywords: [must, should, may, scaffold, init, tasks, verification]
  - id: interfaces
    keywords: [harness-scaffold, hk, mise, routes, lifecycle, export]
  - id: invariants
    keywords: [deterministic, ci-parity, readiness, evidence, integrity]
---

# harness-toolkit specification

This file states the current correctness contract. Design decisions live in
[`docs/reference/decisions/`](docs/reference/decisions/). The generated task
surface lives in the [task contract](docs/reference/task-contract.md).

## Summary

harness-toolkit provides two products that teams can adopt separately:

- `harness-scaffold` generates an agent-ready repository. The repository uses
  native Mise tasks and can select product checks from changed paths.
- `hk` and `harness-kit` record lifecycle evidence for work in an existing
  repository. Generated projects do not need Harness Kit in CI.

## Goals / Non-Goals

Goals:

- Give generated repositories a predictable quality and verification surface.
- Keep orchestration thin and let each stack use its native tools.
- Keep validation, review, and handoff evidence inspectable.
- Use the same native entrypoints in local work and CI.

Non-goals:

- Do not generate the retired `.ai/plans` or slice-workflow contract in new
  repositories.
- Do not turn Harness Kit into a task runner.
- Do not require a local Harness Kit ledger in generated CI.
- Do not infer commands, review quality, or durable context from heuristics.

## Requirements

- `harness-scaffold init` and generated `mise run init` MUST support interactive
  use and deterministic non-interactive use. Invalid or missing required input
  MUST fail with a clear error.
- The scaffold MUST support Python, Go, Rust, Web, Blender, and Three.js.
  It MUST support `single` and `apps` shapes. Blender and Three.js MUST reject
  the `apps` shape. Each stack MUST validate its own options before writing.
- Every generated repository MUST provide executable, described Mise tasks for
  `init`, `setup`, `fmt`, `lint`, `typecheck`, `test`, `build`, `check`, `dev`,
  `ci`, `verify`, and `docs`. These tasks MUST call native stack tools.
- A fresh project MUST pass `mise run check` without manual repair. `mise run
  ci` MUST run the same quality gate. Generated CI and hooks MUST use this task
  surface.
- New projects MUST include `.harness/verification.toml` and
  `scripts/verify-routes`. The route registry MAY start with no routes.
- Each automated route MUST have a unique ID, a descriptive title, and an
  executable script below `scripts/verify`.
- Route execution MUST require an explicit `--route <id>` or `--all` choice.
  `--list` MUST discover routes without running them. The runner MUST NOT infer
  route applicability from changed paths. Manual or credentialed work MUST NOT
  count as an automated pass.
- A product route MUST observe the behavior it claims to prove. It MUST own
  launch, readiness, isolation, cleanup, and useful output. It SHOULD include a
  negative control when that control can disprove a false success.
- Harness Kit lifecycle work MUST retain an explicit plan, relevant context and
  decision impact, validation evidence, review, a readiness result, and a
  rendered handoff.
- `hk validate` MUST record the native command, rationale, result, and evidence.
  It MUST preserve timeout and truncation facts. It MUST redact protected data
  and MUST NOT hide work behind an HK task-runner command.
- HK review evidence MUST come from an independent tool or agent, or from a
  fresh-context subagent. Self-review by the implementation agent MUST NOT
  satisfy readiness. An unavailable reviewer requires an explicit dangerous
  skip with a reason and mitigation.
- HK exports MUST remain generated views of canonical ledger state. A handoff
  directory MUST contain one human-readable view, integrity metadata, and only
  artifacts that were attached explicitly. Integrity checks MUST reject stale,
  malformed, unsafe, or modified exports.
- `mise run check` SHOULD stay fast. Teams SHOULD reserve product proof for
  explicitly selected routes and use `mise run verify -- --route <id>` when
  heavy quality and stack validation belong in the same closeout.
- Generated docs SHOULD keep their machine-readable frontmatter. Architecture
  decision records SHOULD follow the repository's ADR structure.
- HK profiles SHOULD guide focused checks and follow-up reviews. They MUST NOT
  silently alter readiness requirements.
- Teams MAY adopt Harness Kit locally or externally. They MAY commit a generated
  handoff export when durable review context is useful.
- Stacks MAY add native browser, container, integration, or artifact checks.

## Interfaces & Contracts

- `harness-scaffold init` accepts a project name, shape, and stack in
  non-interactive mode. It writes a repository-owned Mise task surface. Stack
  references define stack-specific options.
- `mise run check` is the fast quality entrypoint. Plain `mise run verify` adds
  heavy stack checks. Product routes run only when explicit runner arguments are
  passed after `--`.
- `scripts/verify-routes` supports `--list`, repeatable `--route <id>`, and
  explicit `--all`; these modes are mutually exclusive.
- `.harness/verification.toml` uses version 1. It declares only stable route IDs,
  descriptive titles, and scripts. Agents and engineers choose relevant routes
  from code and product context.
- `hk` is an optional, shell-first lifecycle interface. Profiles and repository
  scripts guide native work. `hk sync --check` reports checkpoint freshness,
  while `hk ready` reports lifecycle readiness.
- Handoff exports follow ADRs
  [0009](docs/reference/decisions/0009-harness-kit-lifecycle-first-cli.md),
  [0010](docs/reference/decisions/0010-compact-hk-export-packages.md), and
  [0011](docs/reference/decisions/0011-path-aware-review-freshness.md).

## Invariants

- **Deterministic initialization:** The same valid non-interactive input MUST
  produce the same output. Generation MUST NOT depend on absolute paths or
  mutable global state.
- **CI parity:** Local `mise run check` MUST match the generated CI quality gate.
  Pull-request CI MUST select product routes from the relevant changed paths.
- **Native ownership:** Generated tasks, route maps, and route scripts belong to
  the generated repository. New projects MUST NOT depend on the retired
  slice-plan workflow.
- **Verification safety:** Automation MUST run only required, configured,
  executable scripts below `scripts/verify`. A route failure MUST fail
  verification.
- **Lifecycle safety:** HK MUST distinguish evidence freshness from sync
  freshness. Readiness MUST report missing or stale proof without heuristic
  scores.
- **Export integrity:** Only the active work's generated export MAY be neutral to
  lifecycle freshness. Export files, hashes, links, and copied artifacts MUST
  remain independently verifiable.

## Acceptance

A change satisfies this contract when applicable contract tests and generated-
project smoke tests prove deterministic initialization, the native task surface,
and CI parity. A fresh supported project must pass `mise run check`.

Verification-route changes also need tests for no-selector, selected-path, and
changed-range behavior. Product routes must demonstrate the observed outcome and
cleanup. Harness Kit changes need tests for readiness, safe validation evidence,
independent review, and export integrity.

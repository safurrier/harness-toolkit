---
id: stack-acceptance-rubric
title: Stack Acceptance Rubric
description: >
  Review rubric for adding or changing language stacks, including required task
  coverage, generated files, E2E tests, smoke matrix expectations, and allowed
  stack-specific deviations.
index:
  - id: required-capabilities
    keywords: [required, capabilities, fmt, lint, typecheck, test, build]
  - id: smoke-matrix
    keywords: [smoke, matrix, ci, generated-project, supported-stack]
  - id: reviewer-checklist
    keywords: [reviewer, checklist, future-stack, acceptance]
---

# Stack Acceptance Rubric

Use this before adding a new supported stack or changing the baseline for an
existing stack. A supported stack is not just a set of templates; it is a
language-specific implementation of the stable mise task contract.

## Required Capabilities

Every supported stack must provide these pieces unless the deviation is
documented in the stack page and accepted in review.

| Area | Required bar |
|---|---|
| Generated files | Single-project and apps-shape init produce a coherent repo layout, generated `SPEC.md`, `AGENTS.md`, docs, skills, `.gitignore`, `.mise.toml`, and CI workflow. |
| Task dispatch | `setup`, `fmt`, `lint`, `typecheck`, `test`, `build`, `check`, `ci`, `verify`, and `dev` route through the stack dispatch helpers. |
| Formatter | `mise run fmt -- --check` or equivalent check mode fails on unformatted code. |
| Linter | `mise run lint` catches at least one real language/tooling mistake. |
| Typecheck | `mise run typecheck` runs the stack's closest static type or compile check. |
| Tests | `mise run test` runs generated tests and writes a CI artifact under the generated test-results directory. |
| Build | `mise run build` performs the stack's release/build path, even if that is a lightweight package build for interpreted stacks. |
| Product verification | Plain `mise run verify` completes stack-specific heavy checks. Named product routes run only when explicitly requested. |

## Smoke Matrix

Repository CI must include every supported stack in the generated-project smoke
matrix. The smoke entry should initialize a generated repo, run setup, and run
the fast gate. Add stack-specific `verify` coverage when the stack introduces a
new runtime, browser, or artifact path:

```bash
mise run init -- --non-interactive --name <name> --stack <stack>
mise run setup
mise run check
scripts/verify-routes --list
mise run verify -- --route <relevant-route-id>
```

A planned stack may stay out of the smoke matrix only while it is clearly marked
as planned and is not offered as a supported `init --stack` value.

## E2E Test Bar

Add or update `tests/e2e/test_<stack>.py` for every supported stack.

The happy path must cover:

- single-project init layout and scaffold cleanup
- generated docs, `SPEC.md`, `AGENTS.md`, skills, and generated CI contract
- `mise run check` and applicable `mise run verify` behavior after setup
- apps-shape init layout and apps-shape `mise run check`

The gate tests must prove the stack tooling fails on real problems:

- formatting failure
- lint failure when the stack has a linter
- typecheck or compile failure
- test failure

Compiled stacks should also validate the release build output. Stacks that ship
a Dockerfile should have Docker validation in `mise run verify`, unless the
stack page records why Docker is intentionally absent.

## Optional Extras

Stack-specific extras are welcome when they fit the language ecosystem:

- Dockerfiles for service-oriented or compiled stacks
- docs generators, API docs, or coverage reports
- browser or runtime smoke tests for web stacks
- package publishing checks

Extras should not replace the required task contract. If an extra is expensive,
put it behind `mise run verify` rather than the fast `mise run check` gate.

## Reviewer Checklist

Use this checklist on future stack PRs:

- The stack is listed in stack docs, `.mise` tool rewriting, init options, and
  stack dispatch registration.
- Single and apps generated repos both pass their happy-path checks.
- Repository CI includes the stack in the smoke matrix when the stack is
  supported.
- The stack has negative-path tests for its formatter, linter, typecheck or
  compile check, and test runner.
- Release build and Docker expectations are either implemented or explicitly
  documented as not applicable.
- Any deviation from this rubric is called out in the plan, ADR or decision
  ledger entry, and PR description.

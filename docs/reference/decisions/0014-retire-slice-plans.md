---
id: decision-retire-slice-plans
title: Retire generated slice-plan workflow
description: Supersedes the generated .ai/plans and slice-workflow task contract.
status: accepted
index:
  - id: decision
    keywords: [scaffold, verification, plans, migration]
---
# ADR 0014 — Retire generated slice-plan workflow

## Decision

New projects no longer receive `.ai/plans`, slice prompt skills, plan-directory
checks, or plan-specific mise tasks. The stable generated contract is native
quality tasks plus optional path-selected product verification routes.

Harness Kit remains an optional lifecycle and handoff tool; it is not required in
generated CI because its ledger can be local or external. Existing generated
repositories retain their old files as legacy projects and are not mutated.

## Consequences

ADRs 0002–0006 describe the historical plan contract and remain evidence of why
it existed. ADR 0009's generated-repository plan compatibility is superseded for
new projects by this decision. Product behavior is proved by route scripts that
observe real outcomes, not by plan-directory completeness.

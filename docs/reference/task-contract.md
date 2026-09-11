---
id: task-contract
title: Scaffold task contract
description: Stable native mise task surface for generated repositories.
index:
  - id: verification-routes
    keywords: [mise, verify, routes, validation]
---
# Scaffold task contract

Every generated repository exposes `setup`, `fmt`, `lint`, `typecheck`, `test`,
`build`, `check`, `dev`, `ci`, `verify`, and `docs` as executable files under
`.mise/tasks/`. `mise run check` is the fast quality gate; `mise run ci` delegates
to it. Task wrappers remain thin adapters over language-native tools.

`mise run verify` is the heavier product-validation entrypoint. It runs `check`
and then stack-specific integration, Docker, artifact, or browser work. Product
routes run only when the caller explicitly passes route arguments.

## Verification routes

The optional `.harness/verification.toml` registry gives executable product
journeys stable names. It does not infer coverage from changed paths.

```bash
scripts/verify-routes --list
scripts/verify-routes --route create-record
scripts/verify-routes --route import-records --route export-records
scripts/verify-routes --all
mise run verify -- --route create-record
```

An agent or engineer chooses relevant routes from code and product context, then
records why those routes cover the change and which material routes were skipped.
Each route follows **Surface, Run, Drive, Observe, Isolate** and owns launch,
readiness, drive, observation, cleanup, and useful artifacts. Manual or
credentialed procedures are handoff obligations rather than automated success.

Plain `mise run verify` deliberately runs the full quality gate and stack-specific
verification without guessing which custom product routes apply. `--all` is an
explicit broad choice, not the default.

Harness Kit is optional for generated repositories. It can record a plan,
validation, independent review, and handoff when a team adopts it, but the
scaffold does not require a local HK ledger in CI.

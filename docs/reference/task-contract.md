---
id: task-contract
title: Scaffold task contract
description: Stable native mise task surface for generated repositories.
index:
  - id: verification-routes
    keywords: [mise, verify, routes, paths, validation]
---
# Scaffold task contract

Every generated repository exposes `setup`, `fmt`, `lint`, `typecheck`, `test`,
`build`, `check`, `dev`, `ci`, `verify`, and `docs` as executable files under
`.mise/tasks/`. `mise run check` is the fast quality gate; `mise run ci` delegates
to it. Task wrappers remain thin adapters over language-native tools.

`mise run verify` is the heavier product-validation entrypoint. It runs `check`,
then stack-specific integration, Docker, artifact, or browser work, then
`scripts/verify-routes` when the repository has it. The optional
`.harness/verification.toml` map selects required routes by changed source paths.

```bash
scripts/verify-routes --path src/service.py
scripts/verify-routes --changed-from origin/main...HEAD
mise run verify -- --changed-from origin/main...HEAD
```

With no selector, every required automated route runs. Route scripts follow **Surface, Run, Drive, Observe, Isolate** and own launch,
readiness, drive, observation, cleanup, and useful artifacts. Manual or
credentialed procedures are handoff obligations rather than CI success.

Harness Kit is optional for generated repositories. It can record a plan,
validation, independent review, and handoff when a team adopts it, but the
scaffold does not require a local HK ledger in CI.

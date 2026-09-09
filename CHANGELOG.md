# Changelog

## Unreleased

- Fix generated Blender `build.py` import ordering so its pinned Ruff quality gate passes after formatting.
- Keep the `WEBGL_lose_context` extension reference through Three.js E2E context loss, because a lost context cannot reliably reacquire it for restoration.
- Add Blender and Three.js single-project visual starters with local task dispatch, editable source seams, reproducible dependency templates, and documented render/browser prerequisites.
- Restore the managed Python/uv runtime for generated Three.js task scripts.
- Pin generated Web peer dependency sets and use managed npm 11.6.2 to avoid npm 10 peer-resolution failures.

## v0.3.0 - 2026-06-10

### Added

- Added the Web scaffold stack for Vite, React, TypeScript, Cloudflare Workers,
  Static Assets, and Cloudflare D1.
- Added opt-in Web stack variants:
  - `--web-ui plain|tailwind|shadcn`
  - `--web-db d1|drizzle-d1`
- Added generated Web stack smoke coverage for single-project and apps workspace
  shapes, including setup, check, build/verify, audit, and module-selector
  behavior.
- Added HK config diagnostics for auditing user/dots/repo Harness Kit config and
  target bindings.
- Added HK system-map parsing, validation, matching, brief/checks views, and
  authoring guidance for component/invariant maps.
- Added path-aware `hk status` freshness diagnostics for validation and review
  evidence, including no-profile generic guidance and required-profile label
  authority.
- Added dogfood regression scenarios for `hk status` freshness behavior.
- Added the "Harness Kit: Dumb Tasks, Smart Agents" docs page explaining HK's
  what/why thesis, lifecycle spine, config layers, skills boundary, and dogfood
  workflow.
- Added a GitHub Pages documentation workflow that builds docs on PRs and
  deploys MkDocs from `main`.

### Changed

- Updated `hk status` to be the default closeout coach: it now surfaces evidence
  freshness, stale changed paths, active export neutrality, and explicit path
  decisions by default.
- Made validation evidence path/content-aware, matching review evidence so small
  follow-up edits can be covered by targeted validation instead of broad reruns.
- Kept required profile check/review labels authoritative while allowing generic
  freshness guidance when no profile is configured.
- Made active HK handoff exports neutral for validation/review freshness and
  source-risk matching while still checking export freshness separately.
- Reorganized MkDocs navigation and docs files into intent-based `explanation/`,
  `how-to`, and `reference/` sections.
- Refreshed README positioning around the "dumb tasks, smart agents" thesis and
  linked the published docs site.
- Updated documentation links, docs routing indexes, and stack references for the
  new Web stack and optional variants.
- Kept generated Web defaults intentionally small: plain CSS plus raw Cloudflare
  D1 prepared statements. Tailwind, shadcn/ui, and Drizzle-D1 are opt-in.

### Fixed

- Prevented generated repos from retaining Harness Toolkit's root-only docs
  publishing workflow.
- Hardened generated Web saved-run routes so remote callers cannot spoof
  `Cf-Access-Authenticated-User-Email`; localhost still uses the explicit
  `local-dev` path.
- Rejected malformed saved-run titles with `400 invalid_run`.
- Escaped generated TSX template literal content for project descriptions.
- Fixed apps-shape Web `mise run dev -- <module> --help` so module names are not
  forwarded to Wrangler as entrypoints.
- Updated generated Vite/Vitest tooling to avoid moderate npm audit findings.

## v0.2.0 - 2026-05-15

### Added

- Added `hk` / `harness-kit`, the portable lifecycle CLI for existing repositories.
- Added ledger-backed lifecycle records for context, plans, decisions, validation evidence, external-enough reviews, sync checkpoints, summaries, and handoff rendering.
- Added configurable HK profile catalogs, target bindings, changed-path check/review suggestions, profile review prompts, and profile resolution across linked Git worktrees.
- Added compact `.ai/hk/<work-id>/` handoff exports with `README.md`, `meta.json`, explicit artifacts, and strict `hk export --check` integrity validation.
- Added artifact attachment support and export metadata suitable for dashboards and review handoffs.
- Added repo-local and generated `harness-kit-profile-authoring` skill guidance for mining validation contracts and avoiding closeout loops.

### Changed

- Made Harness Toolkit’s own workflow HK-native: generated `.ai/hk` exports are the normal committed handoff artifact, while legacy `.ai/plans` remains scaffold/generated-repo compatibility.
- Made active `.ai/hk/<work-id>/` exports lifecycle-neutral for sync, validation/review freshness, readiness changed paths, and profile matching, while preserving non-active export staleness.
- Improved review freshness to track changed-path coverage so targeted follow-up reviews can satisfy readiness after small post-review fixes.
- Updated profile authoring guidance to distinguish focused iteration checks, final closeout gates, heavy/CI parity, handoff/export checks, required reviews, and advisory reviews.
- Updated generated profile templates to discourage broad expensive `required_when = ["*"]` defaults and guide targeted validation/review follow-up.
- Improved CLI/help/docs for install, release, portable workflow adoption, profile reviews, and HK lifecycle design.

### Fixed

- Hardened sync/readiness diagnostics around explicit excludes, source-risk drift, active HK exports, and stale handoff artifacts.
- Tightened export integrity checks for unexpected files, invalid generated text, generated/hash tampering, symlinks, unsafe hash paths, and attached-artifact tampering.
- Preserved user-authored export `Status:` notes while keeping generated export README content stable across export/check cycles.

## v0.1.0 - 2026-05-09

### Added

- Initial GitHub-sourced `agent-scaffold` release before the Harness Toolkit rename and HK portable lifecycle split.
- Provided the original scaffold initializer, generated mise task contract, Python/Go/Rust stack templates, and local development documentation.

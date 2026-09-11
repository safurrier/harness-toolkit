---
name: maintain-project-verification
description: "This skill keeps an existing project verification route truthful when public surfaces, prerequisites, observations, or cleanup change. Use it when verification routes drift or become misleading."
---

# Maintain Project Verification

Reconcile and exercise the smallest affected proof route. Do not silently weaken
an observation to make a route green.

1. Trace changed behavior and consumers across code, configuration, runtime, and
   product boundaries. Inspect available routes with `scripts/verify-routes --list`.
2. Choose relevant route IDs from that evidence. Do not treat filenames, registry
   membership, risk labels, or a previous selection as authoritative coverage.
3. Reconcile readiness, action, observation, isolation, cleanup, and retained
   evidence for each affected route. Keep `.harness/verification.toml` limited to
   stable IDs, titles, and script paths.
4. Run focused routes with repeated `--route <id>` arguments. Use
   `mise run verify -- --route <id>` when the full quality and stack checks also
   belong in closeout; reserve `--all` for intentional broad verification.
5. Challenge changed observations with the original repro, bad input, or another
   safe negative control. Classify failures as product regression, stale
   verification, broken infrastructure, or unavailable authority.
6. In the handoff, name routes run and explain material routes skipped. Preserve
   readable evidence and remove only resources this run owns.

Manual or credentialed procedures are obligations, not automated success. Keep
them out of executable routes and record the actual observation honestly.

---
name: maintain-project-verification
description: "This skill keeps an existing project verification route truthful when public surfaces, prerequisites, observations, or cleanup change. Use it when verification paths drift or become misleading."
---

# Maintain Project Verification

Reconcile and exercise the smallest affected proof route. Do not silently weaken
an observation to make a route green.

1. Trace changed public surfaces and consumers, including configuration and
   runtime boundaries. Read the matching entries in `.harness/verification.toml`.
2. Reconcile source/dependency path globs, readiness, action, observation,
   isolation, cleanup, and retained evidence. Add shared infrastructure paths or
   `always = true` only when the route really must run broadly.
3. Run `scripts/verify-routes --path <path>` for affected paths or
   `--changed-from <ref>` for a diff. Verify selection before interpreting a
   passing route as evidence.
4. Run the route through launch → readiness → public action → observed outcome
   and side effect → cleanup. Challenge changed observations with the original
   repro, bad input, or another safe negative control.
5. Classify failures from evidence: product regression, stale verification,
   broken infrastructure, or unavailable authority. Repair the smallest owned
   route or return a product defect to its implementation owner.
6. Preserve readable evidence and remove only resources this run owns. Update
   `docs/reference/verification.md` only when it already owns an index or a
   new multi-route/operator boundary needs one.

Manual or credentialed procedures are obligations, not automated success. Keep
them out of executable routes and record the actual observation honestly.

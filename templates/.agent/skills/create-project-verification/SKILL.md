---
name: create-project-verification
description: "This skill creates or repairs an executable project verification route when a feature or user journey lacks trustworthy runtime proof. Use it when launch, drive, observation, or cleanup are missing."
---

# Create Project Verification

Create the smallest repeatable proof route for one claim. Do not infer product
semantics or call a build, unit-test count, screenshot, or green exit proof of a
user journey without observing the claimed outcome.

1. Identify the feature or caller journey and the public surface it uses.
2. Define **Surface, Run, Drive, Observe, Isolate**: public interface; launch and
   readiness; caller action; distinguishing output or side effect; owned state,
   credentials, and cleanup.
3. Reuse an existing test or script where it proves the claim. Otherwise add the
   narrowest route script under `scripts/verify/` and register it in
   `.harness/verification.toml` with source/dependency path globs.
4. Exercise launch → readiness → drive → observation → cleanup. Keep logs or
   useful artifacts outside disposable state. Add a safe bad input or failing
   control so the observation is known to be sensitive.
5. Mark a route `required = true` only after it has run successfully. Use
   `scripts/verify-routes --path <changed-path>` while iterating; no selector
   runs every required automated route.
6. Keep manual or credentialed validation as an explicit operator procedure in
   `VALIDATION.md` or `docs/reference/verification.md`; never put it in the
   automated registry as a pass.

Use a focused direct test for pure transformations. Use the actual consumer path
for runtime, browser, protocol, persistence, and artifact claims. Browser claims
need a browser action and visible or stateful assertion; build success is not one.
Create `docs/reference/verification.md` only when several routes or operator
procedures need an index.

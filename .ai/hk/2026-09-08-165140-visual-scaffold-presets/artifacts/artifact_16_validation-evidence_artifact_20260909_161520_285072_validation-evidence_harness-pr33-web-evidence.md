# PR33 Web disposable-validation evidence

## Scope and safety

- Validation targets were fresh copied scaffolds at `/private/tmp/harness-pr33-web-{default,shadcn,drizzle}-proof`, not the source checkout. Each guard recorded canonical source and target paths and rejected a target equal to, or beneath, the source realpath; `MISE_PROJECT_ROOT` was unset before init.
- Init used `UV_NO_CONFIG=1 /Users/alexfurrier/.local/bin/uv run --locked --all-extras harness-scaffold init ...` from the disposable copied scaffold; no `uv --directory` was used. The copy's source `.mise.toml` was removed before init so the command could not enter through source task configuration; init writes the generated configuration.
- All executed target commands had a 180-second subprocess bound. `MISE_TRUSTED_CONFIG_PATHS=/private/tmp` was only an environment variable for disposable target commands, never persisted. Source-root task validation used `MISE_TRUSTED_CONFIG_PATHS=<source-parent>` only for that root `mise run check` command.
- No global npm/mise/uv/tool configuration was edited. `npm config get min-release-age` was `7` before and after. No secrets were printed.

## Scoped npm admission and results

Every disposable npm/mise lifecycle command received `NPM_CONFIG_MIN_RELEASE_AGE=0`; no `--force`, `--legacy-peer-deps`, `--ignore-scripts`, audit fix, or global setting was used. The managed runtime was Node `v22.23.2`, npm `11.6.2`.

- **default:** init, normal scripted `mise run setup` (which executes `npm install --package-lock=false` with scripts), `npm ls sharp --json`, temporary audit-lock materialization, `npm audit --json`, `mise run check`, and `mise run build` all passed.
- `npm ls` resolves `wrangler -> miniflare -> sharp@0.35.4`, marked `overridden: true`.
- The template intentionally has no Web lockfile. Only after the successful normal scripted install, `npm install --package-lock-only` materialized a disposable `package-lock.json` solely to allow audit; this did not change template or lock policy.
- Audit JSON reported `{info:0, low:0, moderate:0, high:0, critical:0, total:0}` and contains no `GHSA` identifier. This preserves all audit findings (there were none); no waiver was used.
- **shadcn:** fresh `--web-ui shadcn --web-db d1` init/setup/check/build passed.
- **drizzle:** fresh `--web-ui plain --web-db drizzle-d1` init/setup/check/build passed.

npm 11.6.2 emitted warnings that its local/global `min-release-age`/`allow-scripts` configuration keys are unknown; the exact scoped environment variable was still supplied only to the disposable commands as authorized. This is a tooling-observability caveat, not a claimed global-policy change.

## Decisions and deferrals

1. **Transitive sharp remediation:** retain root `overrides.sharp: "0.35.4"`; do not add `sharp` as an application dependency. Source regression: `tests/unit/stacks/test_web.py::test_generated_web_manifest_overrides_only_transitive_sharp`.
2. **Age-policy exception:** use only `NPM_CONFIG_MIN_RELEASE_AGE=0` in disposable Web validation commands. Do not modify `~/.npmrc`, scaffold policy, or global npm configuration.
3. **Audit lock:** keep generated Web templates lockless; temporary audit-only lock materialization is disposable and explicitly labelled.
4. **Non-Web distinctions:** retain prior evidence accurately: original Luna Blender rendered/reopened but initially failed generated lint before a fresh-default repair proof; Three.js had an initial formatting intervention and one repair before passing. Fresh default Blender and Three.js later passed setup/check/build/verify; this Web proof does not relabel earlier runs as clean one-shot.

## Post-repair source proof and recovery facts

- `UV_NO_CONFIG=1 uv lock` was authorized only to normalize stale local lock metadata. Comparison with `/tmp/harness-pr33-uv.lock.before` removed only the compatibility `[options]` `exclude-newer`/`exclude-newer-span` metadata; package entries and versions did not change, and the final `uv.lock` equals `HEAD`.
- Root focused proof passed: `UV_NO_CONFIG=1 uv run --locked --all-extras pytest tests/unit/stacks/test_web.py tests/unit/stacks/test_visual.py -n0` — 21 passed.
- Required bounded root gate passed: `PYTEST_ADDOPTS='-n0 tests/unit/stacks/test_visual.py tests/unit/stacks/test_web.py' UV_NO_CONFIG=1 MISE_TRUSTED_CONFIG_PATHS=<source-parent> mise run check` — formatting, lint, typecheck, and the explicit 21 tests passed.
- `git diff --check` passed and `git diff --cached --quiet` confirmed no staged files.

## Research citations

- npm configuration environment-variable mapping: <https://docs.npmjs.com/cli/v11/using-npm/config#environment-variables> (basis for scoped `NPM_CONFIG_MIN_RELEASE_AGE`).
- npm audit JSON behavior: <https://docs.npmjs.com/cli/v11/commands/npm-audit> (basis for preserving raw audit JSON rather than suppressing findings).
- npm `overrides`: <https://docs.npmjs.com/cli/v11/configuring-npm/package-json#overrides> (basis for a root transitive dependency override).
- Local implementation: `stacks/web/project/package.json.tmpl`, `tests/unit/stacks/test_web.py`, and disposable logs retained by HK attachment below.

## PR source manifest / stage candidate

Stage candidate (not staged): `.mise/tasks/build`, `.mise/tasks/verify`, `CHANGELOG.md`, `stacks/blender/build.py`, `stacks/threejs/README.md.tmpl`, `stacks/threejs/package.json.tmpl`, `stacks/threejs/src/main.js`, `stacks/threejs/test/e2e.mjs`, `stacks/web/project/package.json.tmpl`, `tests/unit/stacks/test_visual.py`, `tests/unit/stacks/test_web.py`, and the regenerated current-work `.ai/hk/2026-09-08-165140-visual-scaffold-presets/` export. `tree.json` remains pre-existing untracked and is excluded from the candidate.

No independent reviewer is recorded by this implementation run; the required review gate remains for the parent/reviewer.

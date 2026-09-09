# Luna visual integration evaluation evidence

## Scope identity

- **Tested ancestor:** `c4bde2dbe1600a4aea7239ed40a500fb175ab182`. Both trials began from the visual integration candidate rooted at that ancestor; the toolkit checkout was intentionally already dirty and neither trial modified it.
- **Repaired final template:** the current uncommitted `feat/visual-scaffold-presets` candidate after the targeted lifecycle repairs. It is not the tested ancestor. Its exact source identity is captured separately in `/tmp/harness-visual-source-manifest.sha256` after these repairs.
- **Trial history:** preserved; no trial command, log, archive, or screenshot was rerun or altered for this repair.

## Blender — initial attempt and one repair

Initial: real CLI init and setup passed; `mise run check` and `mise run verify` failed only because `scene.py` needed Ruff formatting; build and Blender reopen passed. One repair ran `uv run ruff format scene.py`; then check, build, and verify passed. The final image and editable blend were inspected and persisted. The source report is the authoritative detail.

- Initial report: `/Users/alexfurrier/.pi-personal/agent/sessions/--Users-alexfurrier-git_repositories-obsidian-vault--/subagent-artifacts/outputs/c1d72e2b-acde-45b0-afc2-e3a77426d40b/harness-luna-blender-initial.md`
- Repair report: `/Users/alexfurrier/.pi-personal/agent/sessions/--Users-alexfurrier-git_repositories-obsidian-vault--/subagent-artifacts/outputs/c1d72e2b-acde-45b0-afc2-e3a77426d40b/harness-luna-blender-final.md`
- Preserved logs/archives: `/tmp/harness-visual-integration-eval/blender/` (`01-init.log`–`07-git-status.log`, `first-attempt-source.tgz`, `hashes.sha256`, `repair-01-format.log`–`repair-05-git-status.log`, `repaired-source.tgz`, `repaired-hashes.sha256`).
- Initial screenshot SHA-256: `16093483c9861fc5c700ff1b4f7cdf50c5e881840aaee8c355cf0a5d0a8a1141`.
- Repaired screenshot SHA-256: `16c9039b6124b204c0f8a4f4cbee24493eccf9055c606a9915f538b22ea66e15`.

## Three.js — initial attempt and one repair

Initial: real CLI init/setup and production build passed; format/check/verify failed, and real Chromium E2E timed out at first collection. One repair fixed the `cells`/`apples` state mismatch and formatted the reported files. Check, build, verify, and Chromium E2E then passed. Four inspected screenshots are preserved. This is browser emulation, not real-phone performance evidence.

- Initial report: `/Users/alexfurrier/.pi-personal/agent/sessions/--Users-alexfurrier-git_repositories-obsidian-vault--/subagent-artifacts/outputs/c1d72e2b-acde-45b0-afc2-e3a77426d40b/harness-luna-threejs-initial.md`
- Repair report: `/Users/alexfurrier/.pi-personal/agent/sessions/--Users-alexfurrier-git_repositories-obsidian-vault--/subagent-artifacts/outputs/c1d72e2b-acde-45b0-afc2-e3a77426d40b/harness-luna-threejs-final.md`
- Preserved logs/archives/screenshots: `/tmp/harness-visual-integration-eval/threejs/` (`initial-attempt.tar.gz`, `final-source.tar.gz`, `source-hash.txt`, `check.log`, `repair-check.log`, `verify.log`, `repair-verify.log`, `final-images/`, `final-image-sha256.txt`).
- Initial command-log SHA-256 values are recorded verbatim in the initial report; final image hashes are in `final-image-sha256.txt` and `final-images/hashes.txt`.

## Source artifact hashes

2e30bb5bc3a8914cf0a2fe3304acf5044bebbbf11fc435841e88b0943bf0aedc  /Users/alexfurrier/.pi-personal/agent/sessions/--Users-alexfurrier-git_repositories-obsidian-vault--/subagent-artifacts/outputs/c1d72e2b-acde-45b0-afc2-e3a77426d40b/harness-luna-blender-initial.md
aaf1960301909e655cd3aa294588c0465a752d3d9853b404ffd84a5ffc6c9b24  /Users/alexfurrier/.pi-personal/agent/sessions/--Users-alexfurrier-git_repositories-obsidian-vault--/subagent-artifacts/outputs/c1d72e2b-acde-45b0-afc2-e3a77426d40b/harness-luna-blender-final.md
961d678caab6ad2b2d3af16af2842c7316aad4238b1574ea8b1dfbbc1bfbff45  /Users/alexfurrier/.pi-personal/agent/sessions/--Users-alexfurrier-git_repositories-obsidian-vault--/subagent-artifacts/outputs/c1d72e2b-acde-45b0-afc2-e3a77426d40b/harness-luna-threejs-initial.md
5c9159c1566a72765f3a4ef515091034c6665e649e02e565a63c55f3a6c71eb4  /Users/alexfurrier/.pi-personal/agent/sessions/--Users-alexfurrier-git_repositories-obsidian-vault--/subagent-artifacts/outputs/c1d72e2b-acde-45b0-afc2-e3a77426d40b/harness-luna-threejs-final.md
da87e7cade6d67894c07c3d01e2dd580a022377e8674e9d546e424ad88a61625  /tmp/harness-visual-integration-eval/blender/first-attempt-source.tgz
ac51d670b68d94ad4a726f593eaedd433396164804439f6897eb5e7349d1ccd1  /tmp/harness-visual-integration-eval/blender/repaired-source.tgz
eb1c73626caae5b134f2c189619eb7bf5e86780257cd00a0a49b1aae4860e49a  /tmp/harness-visual-integration-eval/threejs/initial-attempt.tar.gz
2be0ced7ae91c5806baec0bce684195002f5a49faf6d42fee60de44416df42e2  /tmp/harness-visual-integration-eval/threejs/final-source.tar.gz
8c0a15c5cfee1ca811c07019121834bf12a175229edbcebf6baf3f2b4e2ffec5  /tmp/harness-visual-integration-eval/threejs/final-image-sha256.txt

The absolute paths above are intentionally retained as the source artifacts. This compact report is attached to the active HK work/export so the independent reviewer can verify the exact source-report and archive bytes without replaying the trials.

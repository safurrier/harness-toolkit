import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { mkdtempSync, mkdirSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

test("E2E reports an early server exit without hanging in teardown", () => {
  const root = mkdtempSync(join(tmpdir(), "visual-e2e-exit-"));
  mkdirSync(join(root, "node_modules/.bin"), { recursive: true });
  writeFileSync(join(root, "node_modules/.bin/vite"), "#!/bin/sh\nexit 23\n", {
    mode: 0o755,
  });
  try {
    assert.throws(
      () =>
        execFileSync(
          process.execPath,
          [fileURLToPath(new URL("./e2e.mjs", import.meta.url))],
          { cwd: root, timeout: 15000, stdio: "pipe" },
        ),
      (error) =>
        error.code !== "ETIMEDOUT" &&
        error.status !== null &&
        String(error.stderr).includes("Vite exited before readiness"),
    );
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
}, 20000);

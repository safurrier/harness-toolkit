import { spawn } from "node:child_process";
import { mkdir, writeFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import net from "node:net";
import { chromium } from "playwright";

const port = await new Promise((resolve, reject) => {
  const probe = net.createServer();
  probe.once("error", reject);
  probe.listen(0, "127.0.0.1", () => {
    const { port } = probe.address();
    probe.close(() => resolve(port));
  });
});
const url = `http://127.0.0.1:${port}`,
  captures = [];
const server = spawn(
  "./node_modules/.bin/vite",
  ["--host", "127.0.0.1", "--port", String(port), "--strictPort"],
  { stdio: "pipe" },
);
let serverStopped = false;
const serverExit = new Promise((resolve) => {
  server.once("exit", (code, signal) => {
    serverStopped = true;
    resolve({ code, signal });
  });
  server.once("error", (error) => {
    serverStopped = true;
    resolve({ error: error.message });
  });
});
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
async function ready() {
  for (let attempt = 0; attempt < 40; attempt++) {
    if (serverStopped)
      throw new Error(
        `Vite exited before readiness: ${JSON.stringify(await serverExit)}`,
      );
    try {
      const response = await fetch(url);
      if (response.ok) return;
    } catch {}
    await sleep(250);
  }
  throw new Error("Vite did not become ready");
}
async function capture(page, name) {
  const bytes = await page.screenshot({ path: `test-results/${name}.png` });
  captures.push(
    `${name}.png ${createHash("sha256").update(bytes).digest("hex")}`,
  );
}
async function telemetry(page) {
  return page.evaluate(() => window.visualPrototypeTelemetry);
}
async function keyUntil(page, key, predicate, label) {
  await page.keyboard.down(key);
  try {
    await page.waitForFunction(predicate, undefined, { timeout: 15000 });
  } catch (error) {
    throw new Error(
      `${label}; telemetry=${JSON.stringify(await telemetry(page))}; ${error.message}`,
    );
  } finally {
    await page.keyboard.up(key);
  }
}
async function moveTo(page, target) {
  const current = await telemetry(page);
  if (target.x < current.x)
    await keyUntil(
      page,
      "a",
      `window.visualPrototypeTelemetry.x <= ${target.x}`,
      `did not reach x=${target.x}`,
    );
  if (target.x > current.x)
    await keyUntil(
      page,
      "d",
      `window.visualPrototypeTelemetry.x >= ${target.x}`,
      `did not reach x=${target.x}`,
    );
  const afterX = await telemetry(page);
  if (target.z < afterX.z)
    await keyUntil(
      page,
      "s",
      `window.visualPrototypeTelemetry.z <= ${target.z}`,
      `did not reach z=${target.z}`,
    );
  if (target.z > afterX.z)
    await keyUntil(
      page,
      "w",
      `window.visualPrototypeTelemetry.z >= ${target.z}`,
      `did not reach z=${target.z}`,
    );
}
async function collectAt(page, target, expected) {
  await moveTo(page, target);
  await page.keyboard.press("e");
  await page.waitForFunction(
    (count) => window.visualPrototypeTelemetry.apples === count,
    expected,
    { timeout: 3000 },
  );
}
try {
  await mkdir("test-results", { recursive: true });
  await ready();
  const browser = await chromium.launch(); // Uses Playwright's standard cache discovery; no machine path is baked in.
  try {
    const page = await browser.newPage({
      viewport: { width: 390, height: 844 },
      deviceScaleFactor: 1,
      isMobile: true,
      hasTouch: true,
    });
    const errors = [];
    page.on("pageerror", (error) => errors.push(error.message));
    await page.goto(url, { waitUntil: "domcontentloaded" });
    await page.waitForFunction(
      () => window.visualPrototypeTelemetry?.frames > 2,
      { timeout: 5000 },
    );
    if (await page.locator("#unsupported").isVisible())
      throw new Error("WebGL fallback appeared in normal Chromium run");
    const mobileLayout = await page.evaluate(() => ({
      width: innerWidth,
      overflow: document.documentElement.scrollWidth > innerWidth,
      charset: document.characterSet,
    }));
    if (
      mobileLayout.width !== 390 ||
      mobileLayout.overflow ||
      mobileLayout.charset !== "UTF-8"
    )
      throw new Error(
        `mobile viewport/charset invalid: ${JSON.stringify(mobileLayout)}`,
      );
    await capture(page, "portrait-start");
    await page.locator("canvas").click({ position: { x: 195, y: 420 } });
    // This negative control uses a real key but deliberately never reaches an apple.
    await keyUntil(
      page,
      "w",
      "window.visualPrototypeTelemetry.z >= -3",
      "negative-control movement failed",
    );
    await page.keyboard.press("e");
    if ((await telemetry(page)).apples !== 0)
      throw new Error(
        "negative control collected an apple without reaching one",
      );
    // Real keyboard events follow the public default geometry. Conditions observe state only;
    // they never mutate it, so slow software-rendered Chromium cannot shorten travel.
    await collectAt(page, { x: -3.65, z: 1 }, 1);
    await collectAt(page, { x: 0.35, z: 4 }, 2);
    await collectAt(page, { x: 4.35, z: 0 }, 3);
    await moveTo(page, { x: 0, z: 7 });
    await page.keyboard.press("e");
    const deliveredStatus = await page.locator("#status").textContent();
    if (!deliveredStatus.startsWith("Delivered!"))
      throw new Error(
        `keyboard route did not deliver all apples (${deliveredStatus}); telemetry=${JSON.stringify(await telemetry(page))}`,
      );
    await capture(page, "portrait-delivered");
    await page.getByRole("button", { name: "REPLAY" }).click();
    if (
      !(await page.locator("#status").textContent()).startsWith("Apples: 0/3")
    )
      throw new Error("replay did not reset mission");
    // Two simultaneous real touch contacts exercise joystick and camera without mouse input.
    const box = await page.locator("#joystick").boundingBox();
    const cdp = await page.context().newCDPSession(page);
    await cdp.send("Input.dispatchTouchEvent", {
      type: "touchStart",
      touchPoints: [
        { x: box.x + 41, y: box.y + 41, id: 7 },
        { x: 180, y: 400, id: 9 },
      ],
    });
    await cdp.send("Input.dispatchTouchEvent", {
      type: "touchMove",
      touchPoints: [
        { x: box.x + 72, y: box.y + 41, id: 7 },
        { x: 230, y: 400, id: 9 },
      ],
    });
    await page.waitForFunction(
      () =>
        window.visualPrototypeTelemetry.x > 0.5 &&
        window.visualPrototypeTelemetry.yaw > 0.1,
      undefined,
      { timeout: 5000 },
    );
    await cdp.send("Input.dispatchTouchEvent", {
      type: "touchEnd",
      touchPoints: [],
    });
    await page.locator("canvas").dispatchEvent("pointercancel");
    await page.evaluate(() => window.dispatchEvent(new Event("blur")));
    const before = await telemetry(page);
    await keyUntil(
      page,
      "w",
      `window.visualPrototypeTelemetry.z >= ${before.z + 0.4}`,
      "keyboard did not recover after cancel and blur",
    );
    await page.setViewportSize({ width: 844, height: 390 });
    await page.waitForFunction(
      `window.visualPrototypeTelemetry.frames > ${before.frames + 2}`,
      undefined,
      { timeout: 5000 },
    );
    await capture(page, "landscape-replay");
    if (
      await page.evaluate(
        () =>
          innerWidth !== 844 ||
          document.documentElement.scrollWidth > innerWidth,
      )
    )
      throw new Error("landscape mobile viewport overflow");
    for (const selector of ["#joystick", "#action", "#replay"]) {
      const bounds = await page.locator(selector).boundingBox();
      if (
        !bounds ||
        bounds.x < 0 ||
        bounds.y < 0 ||
        bounds.x + bounds.width > 844 ||
        bounds.y + bounds.height > 390
      )
        throw new Error(`landscape control out of bounds: ${selector}`);
    }
    const desktop = await browser.newPage({
      viewport: { width: 1280, height: 720 },
    });
    desktop.on("pageerror", (error) => errors.push(error.message));
    await desktop.goto(url);
    await desktop.waitForFunction(
      () => window.visualPrototypeTelemetry?.frames > 2,
    );
    await capture(desktop, "desktop-start");
    await keyUntil(
      desktop,
      "w",
      "window.visualPrototypeTelemetry.z >= -3",
      "desktop input failed",
    );
    await desktop.close();
    if (errors.length) throw new Error(`page errors: ${errors.join("; ")}`);
  } finally {
    await browser.close();
  }
  await writeFile("test-results/hashes.txt", `${captures.join("\n")}\n`);
  console.log(captures.join("\n"));
} finally {
  if (!serverStopped) server.kill("SIGTERM");
  await serverExit;
}

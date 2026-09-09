---
id: visual-stacks
title: Visual Stacks
description: >
  Blender and Three.js visual starter stacks: their editable seams, local tooling,
  render or browser validation, and optional local prerequisites.
index:
  - id: blender
    keywords: [blender, render, scene, blend, python-exit-code]
  - id: threejs
    keywords: [threejs, vite, mobile, touch, playwright, browser]
---

# Visual Stacks

Harness Scaffold offers two single-project visual starters. They deliberately use
explicit stack names rather than a generic preset system.

## Blender

```bash
harness-scaffold init --non-interactive --name garden-scene --shape single --stack blender
```

`scene.py` is the editable source and contains a reference brief. `mise run build`
discovers Blender from `BLENDER_BIN` or `PATH`, runs the source once through
`build.py` with `--python-exit-code 1`, then saves `scene.blend` and renders
`scene.png`. Materials set color through Blender nodes. `mise run verify` also
reopens the saved blend. Blender is not installed automatically; install it or set
`BLENDER_BIN` before render, dev, build, or verify commands.

## Three.js

```bash
harness-scaffold init --non-interactive --name visual-game --shape single --stack threejs
```

The backend-free local Vite app has a UTF-8/mobile viewport, safe multi-pointer
touch joystick and camera controls, replay/reset behavior, and a WebGL fallback.
Edit world geometry in `src/main.js`; use `src/style.local.css` for CSS overrides.
The dependency lockfile is generated with the template. Unit rules use native
`node --test`, avoiding a Vitest dependency path. `mise run verify` builds and runs
browser E2E using real keyboard/touch input and read-only telemetry, including an
early Vite-exit assertion. Install Playwright Chromium locally (`npx playwright
install chromium`) only if needed; emulation does not prove real-phone performance.

Neither visual starter supports the apps shape or `--no-examples`; init rejects
those combinations before transforming the scaffold. Rive is an optional future
design-tool consideration only and is not installed or required.

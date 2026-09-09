import "./style.css";
import "./style.local.css";
import * as THREE from "three";
import { clamp, move, collect, deliver } from "./game.js";

const canvas = document.querySelector("canvas"),
  unsupported = document.querySelector("#unsupported");
let renderer;
try {
  renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
} catch (error) {
  unsupported.hidden = false;
  console.error(error);
}
if (renderer) {
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  const scene = new THREE.Scene();
  scene.background = new THREE.Color("#071b2c");
  scene.fog = new THREE.Fog("#071b2c", 12, 35);
  const camera = new THREE.PerspectiveCamera(55, 1, 0.1, 100);
  scene.add(new THREE.HemisphereLight("#bce7ff", "#29351d", 2));
  const sun = new THREE.DirectionalLight("#ffd58a", 2);
  sun.position.set(4, 8, 3);
  scene.add(sun);
  const mat = (color) =>
    new THREE.MeshStandardMaterial({ color, roughness: 0.7 });
  const add = (geo, color, x, z, y = 0, parent = scene) => {
    const mesh = new THREE.Mesh(geo, mat(color));
    mesh.position.set(x, y, z);
    parent.add(mesh);
    return mesh;
  };
  // EDIT SEAM: replace these orchard landmarks and mission coordinates with your own brief.
  add(new THREE.CircleGeometry(28, 48), "#315d38", 0, 0, -0.05).rotation.x =
    -Math.PI / 2;
  const avatar = new THREE.Group();
  avatar.position.set(0, 0, -4);
  scene.add(avatar);
  add(
    new THREE.CapsuleGeometry(0.35, 0.7, 6, 12),
    "#f5d25c",
    0,
    0,
    0.7,
    avatar,
  );
  add(new THREE.SphereGeometry(0.25), "#17243e", 0, -0.27, 1.22, avatar);
  const applePositions = [
    [-4, 1],
    [0, 4],
    [4, 0],
  ];
  const apples = [];
  applePositions.forEach(([x, z]) => {
    add(new THREE.CylinderGeometry(0.18, 0.25, 2), "#754226", x, z, 1);
    apples.push(add(new THREE.SphereGeometry(0.32), "#f04b32", x + 0.35, z, 2));
  });
  const basket = add(
    new THREE.TorusGeometry(0.75, 0.18, 8, 20),
    "#e2ab4c",
    0,
    7,
    0.3,
  );
  basket.rotation.x = Math.PI / 2;
  let input = { x: 0, y: 0 },
    state = { apples: [], delivered: false },
    yaw = 0,
    last = performance.now(),
    frames = 0;
  let joystickPointer = null,
    joystickOrigin = null,
    cameraPointer = null;
  const status = document.querySelector("#status"),
    joy = document.querySelector("#joystick"),
    keys = {};
  function updateStatus() {
    status.textContent = state.delivered
      ? "Delivered! Route complete — REPLAY to go again."
      : `Apples: ${state.apples.length}/3 · collect, then deliver to the gold basket`;
  }
  function resetJoystick() {
    input = { x: 0, y: 0 };
    joystickPointer = null;
    joystickOrigin = null;
    joy.firstElementChild.style.transform = "translate(0,0)";
  }
  function resetAll() {
    resetJoystick();
    cameraPointer = null;
    for (const key of Object.keys(keys)) delete keys[key];
  }
  function replay() {
    resetAll();
    state = { apples: [], delivered: false };
    avatar.position.set(0, 0, -4);
    yaw = 0;
    apples.forEach((apple) => (apple.visible = true));
    updateStatus();
  }
  addEventListener("blur", resetAll);
  addEventListener("pointercancel", resetAll);
  addEventListener("keydown", (event) => {
    keys[event.key] = true;
    if (event.key === "e" || event.key === "E") action();
  });
  addEventListener("keyup", (event) => delete keys[event.key]);
  document.querySelector("#action").onclick = action;
  document.querySelector("#replay").onclick = replay;
  joy.addEventListener("pointerdown", (event) => {
    if (joystickPointer !== null) return;
    joystickPointer = event.pointerId;
    joystickOrigin = { x: event.clientX, y: event.clientY };
    joy.setPointerCapture(event.pointerId);
  });
  joy.addEventListener("pointermove", (event) => {
    if (event.pointerId !== joystickPointer) return;
    const x = clamp((event.clientX - joystickOrigin.x) / 35, -1, 1),
      y = clamp((event.clientY - joystickOrigin.y) / 35, -1, 1);
    input = { x, y: -y };
    joy.firstElementChild.style.transform = `translate(${x * 25}px,${y * 25}px)`;
  });
  for (const type of ["pointerup", "pointercancel"])
    joy.addEventListener(type, (event) => {
      if (event.pointerId === joystickPointer) resetJoystick();
    });
  joy.addEventListener("lostpointercapture", resetJoystick);
  canvas.addEventListener("pointerdown", (event) => {
    if (cameraPointer === null) {
      cameraPointer = { id: event.pointerId, x: event.clientX };
      canvas.setPointerCapture(event.pointerId);
    }
  });
  canvas.addEventListener("pointermove", (event) => {
    if (cameraPointer?.id === event.pointerId) {
      yaw += (event.clientX - cameraPointer.x) * 0.01;
      cameraPointer.x = event.clientX;
    }
  });
  for (const type of ["pointerup", "pointercancel"])
    canvas.addEventListener(type, (event) => {
      if (cameraPointer?.id === event.pointerId) cameraPointer = null;
    });
  canvas.addEventListener("lostpointercapture", () => (cameraPointer = null));
  function horizontalDistance(a, b) {
    return Math.hypot(a.position.x - b.position.x, a.position.z - b.position.z);
  }
  function action() {
    const nearby = apples.find(
      (apple) => apple.visible && horizontalDistance(apple, avatar) < 1.5,
    );
    if (nearby) {
      state = collect(state, nearby);
      nearby.visible = false;
    } else state = deliver(state, horizontalDistance(avatar, basket) < 1.7);
    updateStatus();
  }
  // Read-only browser telemetry lets automated input tests wait for real movement rather than wall-clock sleeps.
  Object.defineProperty(window, "visualPrototypeTelemetry", {
    get: () =>
      Object.freeze({
        x: avatar.position.x,
        z: avatar.position.z,
        apples: state.apples.length,
        delivered: state.delivered,
        frames,
        yaw,
      }),
    configurable: false,
  });
  function frame(now) {
    frames++;
    const dt = Math.min(0.05, (now - last) / 1000);
    last = now;
    const keyboard = {
      x:
        (keys.a || keys.ArrowLeft ? -1 : 0) +
        (keys.d || keys.ArrowRight ? 1 : 0),
      y: (keys.w || keys.ArrowUp ? 1 : 0) + (keys.s || keys.ArrowDown ? -1 : 0),
    };
    const point = move(
      avatar.position,
      { x: input.x + keyboard.x, y: input.y + keyboard.y },
      dt,
    );
    avatar.position.x = clamp(point.x, -8, 8);
    avatar.position.z = clamp(point.z, -8, 8);
    camera.position.set(
      avatar.position.x + Math.sin(yaw) * 8,
      7,
      avatar.position.z - Math.cos(yaw) * 8,
    );
    camera.lookAt(
      avatar.position.x + Math.sin(yaw) * 2,
      0,
      avatar.position.z + Math.cos(yaw) * 2,
    );
    renderer.render(scene, camera);
    requestAnimationFrame(frame);
  }
  addEventListener("resize", () => {
    camera.aspect = innerWidth / innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(innerWidth, innerHeight);
  });
  dispatchEvent(new Event("resize"));
  updateStatus();
  requestAnimationFrame(frame);
}

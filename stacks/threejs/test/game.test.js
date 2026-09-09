import assert from "node:assert/strict";
import test from "node:test";
import { clamp, collect, deliver, move } from "../src/game.js";

test("courier rules preserve bounded movement and delivery requirements", () => {
  assert.equal(clamp(12, -8, 8), 8);
  assert.deepEqual(move({ x: 0, z: 0 }, { x: 1, y: 0 }, 1), { x: 4, z: 0 });
  const apple = {};
  const collected = collect({ apples: [], delivered: false }, apple);
  assert.equal(collected.apples.length, 1);
  assert.equal(deliver(collected, true).delivered, false);
  assert.equal(
    deliver({ ...collected, apples: [apple, {}, {}] }, true).delivered,
    true,
  );
});

export const clamp = (n, a, b) => Math.max(a, Math.min(b, n));
export function normalize(input) {
  const length = Math.hypot(input.x, input.y);
  return length > 1 ? { x: input.x / length, y: input.y / length } : input;
}
export function move(p, input, dt) {
  const direction = normalize(input);
  return { x: p.x + direction.x * dt * 4, z: p.z + direction.y * dt * 4 };
}
export function collect(state, nearApple) {
  return nearApple && !state.apples.includes(nearApple)
    ? { ...state, apples: [...state.apples, nearApple] }
    : state;
}
export function deliver(state, nearBasket) {
  return nearBasket && state.apples.length === 3
    ? { ...state, delivered: true }
    : state;
}

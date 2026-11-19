import { moveTable } from './floorLayout.js';

const KEY_DELTAS = Object.freeze({
  ArrowUp: [0, -2], ArrowDown: [0, 2], ArrowLeft: [-2, 0], ArrowRight: [2, 0],
});

/** Synthetic floor UI feedback only; Python remains authoritative for seating. */
export function keyboardFloorMove(positions, id, key) {
  const delta = KEY_DELTAS[key];
  const point = positions?.[id];
  if (!delta || !point) return null;
  const x = point.x + delta[0];
  const y = point.y + delta[1];
  const next = moveTable(positions, id, x, y);
  const direction = key.slice(5).toLowerCase();
  if (next !== positions) return { positions: next, announcement: `${id} moved ${direction}.` };
  const boundary = x < 10 || x > 90 || y < 10 || y > 90;
  return { positions, announcement: boundary
    ? `${id} cannot move ${direction}: floor-plan boundary.`
    : `${id} cannot move ${direction}: another table is too close.` };
}

import { moveTable } from './floorLayout.js';

const KEY_DELTAS = Object.freeze({
  ArrowUp: [0, -2], ArrowDown: [0, 2], ArrowLeft: [-2, 0], ArrowRight: [2, 0],
});

/** Synthetic floor UI feedback only; Python remains authoritative for seating. */
export function keyboardFloorMove(positions, id, key, shiftKey = false, modifiers = {}) {
  // Preserve browser and assistive-technology shortcuts; only unmodified arrows and Shift+arrows move tables.
  if (modifiers?.altKey || modifiers?.ctrlKey || modifiers?.metaKey) return null;
  const delta = Object.prototype.hasOwnProperty.call(KEY_DELTAS, key) ? KEY_DELTAS[key] : undefined;
  const point = positions && Object.prototype.hasOwnProperty.call(positions, id) ? positions[id] : undefined;
  if (!delta || !point || !Number.isFinite(point.x) || !Number.isFinite(point.y)) return null;
  const step = shiftKey ? 5 : 1;
  const x = point.x + delta[0] * step;
  const y = point.y + delta[1] * step;
  const next = moveTable(positions, id, x, y);
  const direction = key.slice(5).toLowerCase();
  if (next !== positions) return { positions: next, announcement: `${id} moved ${direction}${shiftKey ? ' (large step)' : ''}.` };
  const boundary = x < 10 || x > 90 || y < 10 || y > 90;
  return { positions, announcement: boundary
    ? `${id} cannot move ${direction}: floor-plan boundary.`
    : `${id} cannot move ${direction}: another table is too close.` };
}

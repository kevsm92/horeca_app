import test from 'node:test';
import assert from 'node:assert/strict';
import { pointerFloorPosition } from '../src/pointerFloorPosition.js';

// Synthetic UI geometry only; no physical seating or server-side state.
test('drag distance is invariant when the viewport origin changes', () => {
  const origin = Object.freeze({ x: 35, y: 45 });
  const bounds = Object.freeze({ width: 400, height: 200 });
  const first = pointerFloorPosition(origin, { x: 10, y: 20 }, { x: 90, y: 60 }, bounds);
  const shifted = pointerFloorPosition(origin, { x: 1010, y: 2020 }, { x: 1090, y: 2060 }, bounds);
  assert.deepEqual(first, { x: 55, y: 65 });
  assert.deepEqual(shifted, first);
  assert.deepEqual(origin, { x: 35, y: 45 });
  assert.deepEqual(bounds, { width: 400, height: 200 });
});

test('non-square responsive containers scale horizontal and vertical movement independently', () => {
  const point = pointerFloorPosition({ x: 50, y: 50 }, { x: 0, y: 0 }, { x: 25, y: -25 }, { width: 100, height: 500 });
  assert.deepEqual(point, { x: 75, y: 45 });
});

test('missing pointer geometry is ignored without throwing', () => {
  const valid = { x: 20, y: 30 };
  const bounds = { width: 300, height: 200 };
  assert.equal(pointerFloorPosition(null, valid, valid, bounds), null);
  assert.equal(pointerFloorPosition(valid, null, valid, bounds), null);
  assert.equal(pointerFloorPosition(valid, valid, undefined, bounds), null);
  assert.equal(pointerFloorPosition(valid, valid, valid, null), null);
});

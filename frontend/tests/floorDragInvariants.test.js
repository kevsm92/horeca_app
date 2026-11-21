import test from 'node:test';
import assert from 'node:assert/strict';
import { initialFloorPositions, moveTable } from '../src/floorLayout.js';
import { pointerFloorPosition } from '../src/pointerFloorPosition.js';

// Visual-only synthetic floor positions; no occupancy, seating or API writes.
test('dragging away and back restores the starting visual position', () => {
  const origin = initialFloorPositions.T4;
  const start = Object.freeze({ x: 110, y: 90 });
  const bounds = Object.freeze({ width: 400, height: 250 });
  const outward = pointerFloorPosition(origin, start, { x: 190, y: 140 }, bounds);
  const moved = moveTable(initialFloorPositions, 'T4', outward.x, outward.y);
  const returned = pointerFloorPosition(origin, start, start, bounds);
  const restored = moveTable(moved, 'T4', returned.x, returned.y);
  assert.deepEqual(restored.T4, origin);
  assert.equal(restored.T1, initialFloorPositions.T1);
  assert.deepEqual(start, { x: 110, y: 90 });
  assert.deepEqual(bounds, { width: 400, height: 250 });
});

test('stationary pointer does not allocate a new layout', () => {
  const origin = initialFloorPositions.T2;
  const point = pointerFloorPosition(origin, { x: 10, y: 10 }, { x: 10, y: 10 }, { width: 500, height: 300 });
  assert.equal(moveTable(initialFloorPositions, 'T2', point.x, point.y), initialFloorPositions);
});

test('large finite pointer movements clamp both axes and leave other tables unchanged', () => {
  const point = pointerFloorPosition(initialFloorPositions.T5, { x: 0, y: 0 }, { x: -1e6, y: 1e6 }, { width: 500, height: 500 });
  const moved = moveTable(initialFloorPositions, 'T5', point.x, point.y);
  assert.deepEqual(moved.T5, { x: 10, y: 90 });
  assert.equal(moved.T6, initialFloorPositions.T6);
  assert.deepEqual(initialFloorPositions.T5, { x: 49, y: 49 });
});

import test from 'node:test';
import assert from 'node:assert/strict';
import { initialFloorPositions, moveTable } from '../src/floorLayout.js';
import { pointerFloorPosition } from '../src/pointerFloorPosition.js';

test('pointer movement updates only the targeted visual table', () => {
  const point = pointerFloorPosition(initialFloorPositions.T1, { x: 100, y: 100 }, { x: 150, y: 120 }, { width: 500, height: 200 });
  assert.deepEqual(point, { x: 30, y: 30 });
  const moved = moveTable(initialFloorPositions, 'T1', point.x, point.y);
  assert.deepEqual(moved.T1, { x: 30, y: 30 });
  assert.equal(moved.T2, initialFloorPositions.T2);
  assert.deepEqual(initialFloorPositions.T1, { x: 20, y: 20 });
});

test('off-floor pointer movement clamps visual position without changing other tables', () => {
  const point = pointerFloorPosition(initialFloorPositions.T1, { x: 0, y: 0 }, { x: 1000, y: -1000 }, { width: 100, height: 100 });
  const moved = moveTable(initialFloorPositions, 'T1', point.x, point.y);
  assert.deepEqual(moved.T1, { x: 90, y: 10 });
  assert.equal(moved.T3, initialFloorPositions.T3);
});

test('invalid responsive geometry cannot change the floor layout', () => {
  const point = pointerFloorPosition(initialFloorPositions.T1, { x: 0, y: 0 }, { x: 20, y: 30 }, { width: 0, height: 100 });
  assert.equal(point, null);
  assert.equal(moveTable(initialFloorPositions, 'T1', point?.x, point?.y), initialFloorPositions);
});

test('overflowed pointer geometry cannot propagate to visual positions', () => {
  const point = pointerFloorPosition(initialFloorPositions.T1, { x: -1e308, y: 0 }, { x: 1e308, y: 0 }, { width: 100, height: 100 });
  assert.equal(point, null);
  assert.equal(moveTable(initialFloorPositions, 'T1', point?.x, point?.y), initialFloorPositions);
});

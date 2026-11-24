import test from 'node:test';
import assert from 'node:assert/strict';
import { initialFloorPositions, moveTable } from '../src/floorLayout.js';

// Synthetic visual separation only; never enforces Python seating capacity or authorization.
test('visual collision rejects a diagonal overlap without mutating either table', () => {
  const original = structuredClone(initialFloorPositions);
  const result = moveTable(initialFloorPositions, 'T1', 40, 40);
  assert.equal(result, initialFloorPositions);
  assert.deepEqual(initialFloorPositions, original);
});

test('a table can move when exactly one visual axis is at the minimum gap', () => {
  const layout = Object.freeze({
    T1: Object.freeze({ x: 20, y: 20 }),
    T2: Object.freeze({ x: 40, y: 40 }),
  });
  const moved = moveTable(layout, 'T1', 28, 40);
  assert.notEqual(moved, layout);
  assert.deepEqual(moved.T1, { x: 28, y: 40 });
  assert.equal(moved.T2, layout.T2);
});

test('visual collision is evaluated after boundary clamping', () => {
  const layout = Object.freeze({
    T1: Object.freeze({ x: 50, y: 50 }),
    T2: Object.freeze({ x: 10, y: 90 }),
  });
  assert.equal(moveTable(layout, 'T1', -500, 500), layout);
});

test('malformed other-table positions do not crash valid visual moves', () => {
  const layout = { T1: { x: 20, y: 20 }, T2: null, T3: { x: NaN, y: 40 } };
  const moved = moveTable(layout, 'T1', 30, 30);
  assert.deepEqual(moved.T1, { x: 30, y: 30 });
  assert.equal(moved.T2, null);
  assert.equal(moved.T3, layout.T3);
});

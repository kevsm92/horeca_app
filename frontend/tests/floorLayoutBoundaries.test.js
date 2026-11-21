import test from 'node:test';
import assert from 'node:assert/strict';
import { initialFloorPositions, moveTable } from '../src/floorLayout.js';

test('each arrow direction changes only the requested demo table position', () => {
  for (const [dx, dy] of [[0, -2], [0, 2], [-2, 0], [2, 0]]) {
    const before = initialFloorPositions.T1;
    const after = moveTable(initialFloorPositions, 'T1', before.x + dx, before.y + dy);
    assert.deepEqual(after.T1, { x: before.x + dx, y: before.y + dy });
    assert.equal(after.T2, initialFloorPositions.T2);
    assert.deepEqual(initialFloorPositions.T1, { x: 20, y: 20 });
  }
});

test('repeated movement at every boundary becomes a no-op', () => {
  for (const [x, y, dx, dy] of [[10, 40, -2, 0], [90, 40, 2, 0], [40, 10, 0, -2], [40, 90, 0, 2]]) {
    const atEdge = moveTable(initialFloorPositions, 'T1', x, y);
    assert.equal(moveTable(atEdge, 'T1', x + dx, y + dy), atEdge);
  }
});

test('fractional pointer movement is finite and does not mutate the source', () => {
  const moved = moveTable(initialFloorPositions, 'T3', 78.25, 49.75);
  assert.deepEqual(moved.T3, { x: 78.25, y: 49.75 });
  assert.deepEqual(initialFloorPositions.T3, { x: 78, y: 20 });
});

test('invalid pointer coordinates and missing IDs cannot change layout', () => {
  for (const [id, x, y] of [['T1', NaN, 50], ['T1', 50, Infinity], ['T1', -Infinity, 50], ['unknown', 50, 50]]) {
    assert.equal(moveTable(initialFloorPositions, id, x, y), initialFloorPositions);
  }
});

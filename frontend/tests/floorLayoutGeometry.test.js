import test from 'node:test';
import assert from 'node:assert/strict';
import { initialFloorPositions, moveTable } from '../src/floorLayout.js';

// Visual-only geometry: physical seats, tenant authorization and persistence belong to Python.
test('pointer moves clamp synthetic table centers and preserve original state', () => {
  const original = Object.freeze({ T1: Object.freeze({ x: 50, y: 50 }) });
  for (const [x, y, expected] of [
    [-500, 50, { x: 10, y: 50 }],
    [500, 50, { x: 90, y: 50 }],
    [50, -500, { x: 50, y: 10 }],
    [50, 500, { x: 50, y: 90 }],
  ]) assert.deepEqual(moveTable(original, 'T1', x, y).T1, expected);
  assert.deepEqual(original.T1, { x: 50, y: 50 });
});

test('visual collision blocks movement without changing either table', () => {
  const original = Object.freeze({
    T1: Object.freeze({ x: 20, y: 20 }),
    T2: Object.freeze({ x: 40, y: 40 }),
  });
  assert.equal(moveTable(original, 'T1', 29, 29), original);
  assert.deepEqual(moveTable(original, 'T1', 28, 29).T1, { x: 28, y: 29 });
  assert.deepEqual(original.T2, { x: 40, y: 40 });
});

test('unknown IDs, inherited IDs and invalid pointer coordinates fail closed', () => {
  const original = Object.freeze({ T1: Object.freeze({ x: 20, y: 20 }) });
  assert.equal(moveTable(original, 'missing', 30, 30), original);
  const inherited = Object.create({ T1: { x: 20, y: 20 } });
  assert.equal(moveTable(inherited, 'T1', 30, 30), inherited);
  for (const [x, y] of [[NaN, 20], [20, Infinity], [undefined, 20]]) {
    assert.equal(moveTable(original, 'T1', x, y), original);
  }
});

test('initial synthetic floor centers are in bounds and do not overlap', () => {
  const entries = Object.entries(initialFloorPositions);
  assert.equal(entries.length, 8);
  for (const [id, point] of entries) {
    assert.ok(point.x >= 10 && point.x <= 90 && point.y >= 10 && point.y <= 90, id);
    assert.equal(moveTable(initialFloorPositions, id, point.x, point.y), initialFloorPositions);
    for (const [otherId, other] of entries) {
      if (id !== otherId) assert.ok(
        Math.abs(point.x - other.x) >= 12 || Math.abs(point.y - other.y) >= 12, id
      );
    }
  }
});

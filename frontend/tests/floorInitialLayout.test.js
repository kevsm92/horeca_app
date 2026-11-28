import test from 'node:test';
import assert from 'node:assert/strict';
import { initialFloorPositions, moveTable } from '../src/floorLayout.js';

// Synthetic presentation layout only: physical seating and capacity are Python-owned.
test('initial demo floor has eight distinct, bounded, nonoverlapping table controls', () => {
  const entries = Object.entries(initialFloorPositions);
  assert.equal(entries.length, 8);
  assert.deepEqual(entries.map(([id]) => id), Array.from({ length: 8 }, (_, i) => `T${i + 1}`));
  for (const [id, point] of entries) {
    assert.ok(Number.isFinite(point.x) && point.x >= 10 && point.x <= 90, `${id} x is in bounds`);
    assert.ok(Number.isFinite(point.y) && point.y >= 10 && point.y <= 90, `${id} y is in bounds`);
    for (const [otherId, other] of entries) {
      if (id === otherId) continue;
      assert.ok(Math.abs(point.x - other.x) >= 12 || Math.abs(point.y - other.y) >= 12,
        `${id} and ${otherId} do not overlap`);
    }
  }
});

test('each initial demo table can be moved independently without mutating seed positions', () => {
  const seed = structuredClone(initialFloorPositions);
  for (const [id, point] of Object.entries(initialFloorPositions)) {
    const moved = moveTable(initialFloorPositions, id, point.x + 2, point.y);
    assert.notEqual(moved, initialFloorPositions, `${id} can move right by one keyboard step`);
    assert.deepEqual(moved[id], { x: point.x + 2, y: point.y });
    for (const otherId of Object.keys(seed).filter(otherId => otherId !== id)) {
      assert.equal(moved[otherId], initialFloorPositions[otherId]);
    }
  }
  assert.deepEqual(initialFloorPositions, seed);
});

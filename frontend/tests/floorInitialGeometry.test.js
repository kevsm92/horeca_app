import test from 'node:test';
import assert from 'node:assert/strict';
import { initialFloorPositions, moveTable } from '../src/floorLayout.js';

// Synthetic visual geometry only; Python controls real seating and table inventory.
test('all initial demo table centers fit the editable floor and meet visual separation', () => {
  const entries = Object.entries(initialFloorPositions);
  assert.deepEqual(entries.map(([id]) => id), Array.from({ length: 8 }, (_, i) => `T${i + 1}`));
  for (const [id, point] of entries) {
    assert.ok(Number.isFinite(point.x) && Number.isFinite(point.y), `${id} has finite coordinates`);
    assert.ok(point.x >= 10 && point.x <= 90 && point.y >= 10 && point.y <= 90, `${id} fits within the floor`);
    for (const [otherId, other] of entries) {
      if (id === otherId) continue;
      assert.ok(Math.abs(point.x - other.x) >= 12 || Math.abs(point.y - other.y) >= 12,
        `${id} does not visually overlap ${otherId}`);
    }
  }
});

test('invalid visual moves cannot add a table or corrupt the demo layout', () => {
  const positions = Object.freeze({ T1: Object.freeze({ x: 20, y: 20 }) });
  for (const [id, x, y] of [
    ['T2', 40, 40], ['T1', NaN, 20], ['T1', 20, -Infinity],
    ['T1', '40', 40], ['T1', null, 40], ['T1', 40, undefined]
  ]) {
    assert.strictEqual(moveTable(positions, id, x, y), positions);
  }
  assert.deepEqual(positions, { T1: { x: 20, y: 20 } });
});

import test from 'node:test';
import assert from 'node:assert/strict';
import { initialFloorPositions, moveTable } from '../src/floorLayout.js';

// Synthetic presentation geometry only; Python owns real table capacity and seating.
test('deterministic pointer-move sequence preserves floor geometry invariants', () => {
  let positions = initialFloorPositions;
  let seed = 20261125;
  const random = () => {
    seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0;
    return seed / 0x100000000;
  };
  const ids = Object.keys(positions);
  for (let iteration = 0; iteration < 1200; iteration++) {
    const id = ids[Math.floor(random() * ids.length)];
    const x = random() * 240 - 70;
    const y = random() * 240 - 70;
    const before = positions;
    const snapshot = JSON.stringify(before);
    positions = moveTable(before, id, x, y);
    assert.equal(JSON.stringify(before), snapshot, 'input must never be mutated');
    assert.deepEqual(Object.keys(positions), ids, 'visual movement cannot add/remove tables');
    for (const [tableId, point] of Object.entries(positions)) {
      assert.ok(Number.isFinite(point.x) && point.x >= 10 && point.x <= 90, tableId);
      assert.ok(Number.isFinite(point.y) && point.y >= 10 && point.y <= 90, tableId);
      for (const [otherId, other] of Object.entries(positions)) {
        if (tableId === otherId) continue;
        assert.ok(Math.abs(point.x - other.x) >= 12 || Math.abs(point.y - other.y) >= 12,
          `${tableId} overlaps ${otherId} after move ${iteration}`);
      }
    }
  }
});

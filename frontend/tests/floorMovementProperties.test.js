import test from 'node:test';
import assert from 'node:assert/strict';
import { moveTable, initialFloorPositions } from '../src/floorLayout.js';

// Deterministic synthetic UI invariant checks; not a substitute for Python seating validation.
test('demo drag movements preserve immutable state, bounds and nonoverlapping centers', () => {
  let seed = 20261120;
  const random = () => { seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0; return seed / 4294967296; };
  let positions = structuredClone(initialFloorPositions);
  const ids = Object.keys(positions);
  let accepted = 0;
  let rejected = 0;
  for (let i = 0; i < 1000; i++) {
    const id = ids[Math.floor(random() * ids.length)];
    const x = random() * 160 - 30;
    const y = random() * 160 - 30;
    const before = structuredClone(positions);
    const next = moveTable(positions, id, x, y);
    assert.deepEqual(positions, before, 'original positions must never mutate');
    if (next === positions) { rejected++; continue; }
    accepted++;
    assert.notEqual(next[id], positions[id]);
    for (const otherId of ids.filter(key => key !== id)) assert.equal(next[otherId], positions[otherId]);
    assert.ok(next[id].x >= 10 && next[id].x <= 90);
    assert.ok(next[id].y >= 10 && next[id].y <= 90);
    for (const otherId of ids.filter(key => key !== id)) {
      const other = next[otherId];
      assert.ok(Math.abs(next[id].x - other.x) >= 12 || Math.abs(next[id].y - other.y) >= 12,
        `${id} overlaps ${otherId}`);
    }
    positions = next;
  }
  assert.ok(accepted > 0 && rejected > 0, 'exercise both movement outcomes');
});

import test from 'node:test';
import assert from 'node:assert/strict';
import { moveTable, initialFloorPositions } from '../src/floorLayout.js';

// UI-only immutability checks; Python remains the source of truth for seating.
test('successful movement works with deeply frozen demo positions', () => {
  const frozen = Object.freeze(Object.fromEntries(Object.entries(initialFloorPositions)
    .map(([id, point]) => [id, Object.freeze({ ...point })])));
  const next = moveTable(frozen, 'T1', 10, 10);
  assert.notEqual(next, frozen);
  assert.deepEqual(next.T1, { x: 10, y: 10 });
  assert.deepEqual(frozen.T1, { x: 20, y: 20 });
  for (const id of Object.keys(frozen).filter(id => id !== 'T1')) {
    assert.equal(next[id], frozen[id]);
  }
});

test('rejected collision leaves frozen state unchanged', () => {
  const frozen = Object.freeze({ T1: Object.freeze({ x: 20, y: 20 }), T2: Object.freeze({ x: 50, y: 50 }) });
  assert.equal(moveTable(frozen, 'T1', 50, 50), frozen);
});

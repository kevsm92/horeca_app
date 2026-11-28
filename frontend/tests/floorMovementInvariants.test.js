import test from 'node:test';
import assert from 'node:assert/strict';
import {initialFloorPositions, moveTable} from '../src/floorLayout.js';

// Synthetic UI geometry only; Python owns seating capacity and authorization.
test('each demo table remains within floor bounds after extreme pointer movement', () => {
  for (const id of Object.keys(initialFloorPositions)) {
    for (const [x, y] of [[-1e6, -1e6], [1e6, 1e6], [-1e6, 1e6], [1e6, -1e6]]) {
      const next = moveTable(initialFloorPositions, id, x, y);
      assert.deepEqual(Object.keys(next), Object.keys(initialFloorPositions));
      assert.ok(next[id].x >= 10 && next[id].x <= 90);
      assert.ok(next[id].y >= 10 && next[id].y <= 90);
    }
  }
});

test('collision rejection is symmetric for all distinct demo table pairs', () => {
  for (const [id, point] of Object.entries(initialFloorPositions)) {
    for (const [otherId, other] of Object.entries(initialFloorPositions)) {
      if (id === otherId) continue;
      assert.equal(moveTable(initialFloorPositions, id, other.x, other.y), initialFloorPositions,
        `${id} must not move onto ${otherId}`);
    }
  }
});

test('successful movement preserves all other position references and original state', () => {
  const snapshot = structuredClone(initialFloorPositions);
  const moved = moveTable(initialFloorPositions, 'T1', 10, 10);
  assert.notEqual(moved, initialFloorPositions);
  assert.deepEqual(moved.T1, {x: 10, y: 10});
  for (const id of Object.keys(initialFloorPositions).filter(id => id !== 'T1')) {
    assert.equal(moved[id], initialFloorPositions[id]);
  }
  assert.deepEqual(initialFloorPositions, snapshot);
});

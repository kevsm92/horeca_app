import test from 'node:test';
import assert from 'node:assert/strict';
import {initialFloorPositions, moveTable} from '../src/floorLayout.js';

// These checks cover the geometry used by the demo floor-plan arrow-key handler.
// They do not authorize seating changes or persist any venue layout.
test('repeated arrow-key steps stop at the visible room boundary', () => {
  let positions = initialFloorPositions;
  for (let step = 0; step < 100; step += 1) {
    const current = positions.T1;
    positions = moveTable(positions, 'T1', current.x - 2, current.y);
  }
  assert.deepEqual(positions.T1, {x:10, y:20});
  assert.equal(moveTable(positions, 'T1', 8, 20), positions);
  assert.equal(initialFloorPositions.T1.x, 20);
});

test('diagonal keyboard sequences preserve other tables and clamp both axes', () => {
  let positions = initialFloorPositions;
  for (let step = 0; step < 100; step += 1) {
    const current = positions.T1;
    positions = moveTable(positions, 'T1', current.x + 2, current.y + 2);
  }
  assert.deepEqual(positions.T1, {x:90, y:90});
  for (const id of Object.keys(initialFloorPositions).filter(id => id !== 'T1')) {
    assert.equal(positions[id], initialFloorPositions[id]);
  }
});

test('invalid keyboard movement never corrupts visual positions', () => {
  const positions = moveTable(initialFloorPositions, 'T1', 22, 20);
  assert.equal(moveTable(positions, 'T1', Number.NaN, 22), positions);
  assert.equal(moveTable(positions, 'T1', 24, Number.POSITIVE_INFINITY), positions);
  assert.deepEqual(positions.T1, {x:22, y:20});
});

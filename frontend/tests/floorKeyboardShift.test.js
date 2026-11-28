import test from 'node:test';
import assert from 'node:assert/strict';
import { keyboardFloorMove } from '../src/floorKeyboardMove.js';

test('Shift-arrow moves ten percentage points without changing normal two-point steps', () => {
  const positions = { T1: { x: 20, y: 20 }, T2: { x: 50, y: 50 } };
  const large = keyboardFloorMove(positions, 'T1', 'ArrowRight', true);
  assert.deepEqual(large.positions.T1, { x: 30, y: 20 });
  assert.equal(large.announcement, 'T1 moved right (large step).');
  assert.deepEqual(keyboardFloorMove(positions, 'T1', 'ArrowRight').positions.T1, { x: 22, y: 20 });
  assert.deepEqual(positions.T1, { x: 20, y: 20 });
});

test('Shift-arrow respects boundaries and visual collision protection', () => {
  const boundary = { T1: { x: 90, y: 20 } };
  assert.equal(keyboardFloorMove(boundary, 'T1', 'ArrowRight', true).announcement,
    'T1 cannot move right: floor-plan boundary.');
  assert.strictEqual(keyboardFloorMove(boundary, 'T1', 'ArrowRight', true).positions, boundary);
  const collision = { T1: { x: 20, y: 20 }, T2: { x: 39, y: 20 } };
  const blocked = keyboardFloorMove(collision, 'T1', 'ArrowRight', true);
  assert.strictEqual(blocked.positions, collision);
  assert.equal(blocked.announcement, 'T1 cannot move right: another table is too close.');
});

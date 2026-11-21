import test from 'node:test';
import assert from 'node:assert/strict';
import { keyboardFloorMove } from '../src/floorKeyboardMove.js';

test('keyboard movement clamps at the edge and reports actual partial movement', () => {
  const original = { T1: { x: 89, y: 50 }, T2: { x: 30, y: 30 } };
  const moved = keyboardFloorMove(original, 'T1', 'ArrowRight');
  assert.deepEqual(moved.positions.T1, { x: 90, y: 50 });
  assert.equal(moved.announcement, 'T1 moved right.');
  assert.strictEqual(moved.positions.T2, original.T2);
  assert.deepEqual(original.T1, { x: 89, y: 50 });
  const blocked = keyboardFloorMove(moved.positions, 'T1', 'ArrowRight');
  assert.strictEqual(blocked.positions, moved.positions);
  assert.equal(blocked.announcement, 'T1 cannot move right: floor-plan boundary.');
});

test('large keyboard step reports collision rather than boundary when target is inside floor', () => {
  const original = { T1: { x: 70, y: 50 }, T2: { x: 81, y: 50 } };
  const blocked = keyboardFloorMove(original, 'T1', 'ArrowRight', true);
  assert.strictEqual(blocked.positions, original);
  assert.equal(blocked.announcement, 'T1 cannot move right: another table is too close.');
});

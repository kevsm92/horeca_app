import test from 'node:test';
import assert from 'node:assert/strict';
import { keyboardFloorMove } from '../src/floorKeyboardMove.js';

// Browser-only synthetic floor feedback. Python remains the sole seating authority.
test('blocked arrow movements announce collision without changing frozen geometry', () => {
  const positions = Object.freeze({
    T1: Object.freeze({ x: 40, y: 40 }),
    T2: Object.freeze({ x: 53, y: 40 }),
  });
  const result = keyboardFloorMove(positions, 'T1', 'ArrowRight');
  assert.equal(result.positions, positions);
  assert.equal(result.announcement, 'T1 cannot move right: another table is too close.');
  assert.deepEqual(positions.T1, { x: 40, y: 40 });
});

test('blocked arrows announce each floor boundary without mutating state', () => {
  const cases = [
    ['ArrowLeft', { x: 10, y: 50 }, 'left'],
    ['ArrowRight', { x: 90, y: 50 }, 'right'],
    ['ArrowUp', { x: 50, y: 10 }, 'up'],
    ['ArrowDown', { x: 50, y: 90 }, 'down'],
  ];
  for (const [key, point, direction] of cases) {
    const positions = Object.freeze({ T1: Object.freeze(point) });
    const result = keyboardFloorMove(positions, 'T1', key);
    assert.equal(result.positions, positions);
    assert.equal(result.announcement, `T1 cannot move ${direction}: floor-plan boundary.`);
  }
});

test('successful movement announces direction and respects immutable input', () => {
  const positions = Object.freeze({ T1: Object.freeze({ x: 50, y: 50 }) });
  const result = keyboardFloorMove(positions, 'T1', 'ArrowLeft');
  assert.deepEqual(result.positions.T1, { x: 48, y: 50 });
  assert.equal(result.announcement, 'T1 moved left.');
  assert.deepEqual(positions.T1, { x: 50, y: 50 });
});

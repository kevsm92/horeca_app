import test from 'node:test';
import assert from 'node:assert/strict';
import { keyboardFloorMove } from '../src/floorKeyboardMove.js';

test('all four room edges announce blocked movement without changing frozen positions', () => {
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

test('large-step collision is announced and preserves the existing layout', () => {
  const positions = Object.freeze({
    T1: Object.freeze({ x: 30, y: 30 }),
    T2: Object.freeze({ x: 45, y: 30 }),
  });
  const result = keyboardFloorMove(positions, 'T1', 'ArrowRight', true);
  assert.equal(result.positions, positions);
  assert.equal(result.announcement, 'T1 cannot move right: another table is too close.');
});

test('moving to an exact non-overlapping center-gap boundary is allowed', () => {
  const positions = Object.freeze({
    T1: Object.freeze({ x: 30, y: 30 }),
    T2: Object.freeze({ x: 44, y: 30 }),
  });
  const result = keyboardFloorMove(positions, 'T1', 'ArrowRight');
  assert.deepEqual(result.positions.T1, { x: 32, y: 30 });
  assert.equal(result.announcement, 'T1 moved right.');
  assert.deepEqual(positions.T1, { x: 30, y: 30 });
});

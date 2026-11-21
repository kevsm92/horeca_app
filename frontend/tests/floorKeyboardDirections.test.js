import test from 'node:test';
import assert from 'node:assert/strict';
import { keyboardFloorMove } from '../src/floorKeyboardMove.js';

test('all four arrows move only the selected synthetic table and announce direction', () => {
  const original = Object.freeze({
    T1: Object.freeze({ x: 40, y: 40 }),
    T2: Object.freeze({ x: 80, y: 80 }),
  });
  for (const [key, x, y, direction] of [
    ['ArrowUp', 40, 38, 'up'],
    ['ArrowDown', 40, 42, 'down'],
    ['ArrowLeft', 38, 40, 'left'],
    ['ArrowRight', 42, 40, 'right'],
  ]) {
    const result = keyboardFloorMove(original, 'T1', key);
    assert.deepEqual(result.positions.T1, { x, y });
    assert.strictEqual(result.positions.T2, original.T2);
    assert.equal(result.announcement, `T1 moved ${direction}.`);
    assert.deepEqual(original.T1, { x: 40, y: 40 });
  }
});

test('unrecognized keys and unknown tables are ignored without changing state', () => {
  const positions = { T1: { x: 40, y: 40 } };
  for (const key of ['Enter', 'Escape', 'ArrowDiagonal', '', undefined]) {
    assert.equal(keyboardFloorMove(positions, 'T1', key), null);
  }
  assert.equal(keyboardFloorMove(positions, 'missing', 'ArrowRight'), null);
  assert.equal(keyboardFloorMove(positions, 'T1', 'ArrowRight', false)?.positions.T1.x, 42);
  assert.deepEqual(positions, { T1: { x: 40, y: 40 } });
});

test('all four large-step arrows announce true floor boundaries', () => {
  for (const [key, point, direction] of [
    ['ArrowUp', { x: 50, y: 10 }, 'up'],
    ['ArrowDown', { x: 50, y: 90 }, 'down'],
    ['ArrowLeft', { x: 10, y: 50 }, 'left'],
    ['ArrowRight', { x: 90, y: 50 }, 'right'],
  ]) {
    const positions = { T1: point };
    const result = keyboardFloorMove(positions, 'T1', key, true);
    assert.strictEqual(result.positions, positions);
    assert.equal(result.announcement, `T1 cannot move ${direction}: floor-plan boundary.`);
  }
});

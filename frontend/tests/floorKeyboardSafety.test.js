import test from 'node:test';
import assert from 'node:assert/strict';
import { keyboardFloorMove } from '../src/floorKeyboardMove.js';

test('does not move inherited table identifiers or invalid coordinates', () => {
  const inherited = Object.create({ T1: { x: 20, y: 20 } });
  assert.equal(keyboardFloorMove(inherited, 'T1', 'ArrowRight'), null);
  for (const point of [{ x: NaN, y: 20 }, { x: 20, y: Infinity }, null]) {
    assert.equal(keyboardFloorMove({ T1: point }, 'T1', 'ArrowRight'), null);
  }
});

test('rejects non-arrow and prototype property names without changing positions', () => {
  const positions = Object.freeze({ T1: Object.freeze({ x: 20, y: 20 }) });
  for (const key of ['toString', 'constructor', '__proto__', ' ', 'ArrowRightExtra']) {
    assert.equal(keyboardFloorMove(positions, 'T1', key), null);
  }
  assert.deepEqual(positions.T1, { x: 20, y: 20 });
});

test('collision reports blocked keyboard movement without modifying either table', () => {
  const positions = Object.freeze({
    T1: Object.freeze({ x: 20, y: 20 }),
    T2: Object.freeze({ x: 33, y: 20 }),
  });
  const result = keyboardFloorMove(positions, 'T1', 'ArrowRight');
  assert.equal(result.positions, positions);
  assert.match(result.announcement, /another table is too close/);
  assert.deepEqual(positions.T2, { x: 33, y: 20 });
});

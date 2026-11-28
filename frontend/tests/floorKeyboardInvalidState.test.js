import test from 'node:test';
import assert from 'node:assert/strict';
import { keyboardFloorMove } from '../src/floorKeyboardMove.js';

test('keyboard movement ignores inherited table IDs and prototype key names', () => {
  const positions = Object.create({ inherited: { x: 40, y: 40 } });
  positions.T1 = { x: 30, y: 30 };
  assert.equal(keyboardFloorMove(positions, 'inherited', 'ArrowRight'), null);
  assert.equal(keyboardFloorMove(positions, 'T1', 'toString'), null);
  assert.equal(keyboardFloorMove(positions, 'T1', 'constructor'), null);
  assert.deepEqual(keyboardFloorMove(positions, 'T1', 'ArrowRight').positions.T1, { x: 32, y: 30 });
});

test('keyboard movement ignores malformed synthetic coordinates rather than reporting collisions', () => {
  for (const point of [{ x: NaN, y: 40 }, { x: 40, y: Infinity }, { x: '40', y: 40 }, { x: undefined, y: 40 }]) {
    const positions = { T1: point };
    assert.equal(keyboardFloorMove(positions, 'T1', 'ArrowRight'), null);
    assert.strictEqual(positions.T1, point);
  }
});

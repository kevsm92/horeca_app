import test from 'node:test';
import assert from 'node:assert/strict';
import { keyboardFloorMove } from '../src/floorKeyboardMove.js';

test('modified arrow shortcuts are left to the browser and assistive technology', () => {
  const positions = Object.freeze({ T1: Object.freeze({ x: 40, y: 40 }) });
  for (const modifier of ['altKey', 'ctrlKey', 'metaKey']) {
    for (const key of ['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight']) {
      assert.equal(keyboardFloorMove(positions, 'T1', key, false, { [modifier]: true }), null);
    }
  }
  assert.deepEqual(positions.T1, { x: 40, y: 40 });
});

test('Shift+arrow moves by a larger step and announces it without mutating input', () => {
  const positions = Object.freeze({ T1: Object.freeze({ x: 40, y: 40 }) });
  const result = keyboardFloorMove(positions, 'T1', 'ArrowDown', true);
  assert.deepEqual(result.positions.T1, { x: 40, y: 50 });
  assert.equal(result.announcement, 'T1 moved down (large step).');
  assert.deepEqual(positions.T1, { x: 40, y: 40 });
});

test('invalid floor coordinates and unrelated keyboard commands are ignored', () => {
  const invalid = { T1: { x: Number.NaN, y: 30 } };
  assert.equal(keyboardFloorMove(invalid, 'T1', 'ArrowUp'), null);
  assert.equal(keyboardFloorMove({ T1: { x: 30, y: 30 } }, 'T1', 'Tab'), null);
});

import test from 'node:test';
import assert from 'node:assert/strict';
import { keyboardFloorMove } from '../src/floorKeyboardMove.js';

test('all arrow directions preserve modified browser shortcuts, including Shift combinations', () => {
  const positions = Object.freeze({T1: Object.freeze({x: 50, y: 50})});
  for (const key of ['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight']) {
    for (const shift of [false, true]) {
      for (const modifier of ['altKey', 'ctrlKey', 'metaKey']) {
        assert.equal(keyboardFloorMove(positions, 'T1', key, shift, {[modifier]: true}), null,
          `${modifier}+${shift ? 'Shift+' : ''}${key} must be left to the browser`);
      }
    }
  }
  assert.deepEqual(positions.T1, {x: 50, y: 50});
});

test('unmodified arrows still work after ignored shortcuts', () => {
  const positions = Object.freeze({T1: Object.freeze({x: 50, y: 50})});
  assert.equal(keyboardFloorMove(positions, 'T1', 'ArrowUp', true, {ctrlKey: true}), null);
  const result = keyboardFloorMove(positions, 'T1', 'ArrowUp', true, {ctrlKey: false});
  assert.deepEqual(result.positions.T1, {x: 50, y: 40});
  assert.equal(result.announcement, 'T1 moved up (large step).');
  assert.deepEqual(positions.T1, {x: 50, y: 50});
});

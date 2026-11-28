import test from 'node:test';
import assert from 'node:assert/strict';
import { keyboardFloorMove } from '../src/floorKeyboardMove.js';

test('browser and assistive technology modifier shortcuts never reposition demo tables', () => {
  const positions = { T1: { x: 50, y: 50 }, T2: { x: 80, y: 80 } };
  for (const key of ['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight']) {
    for (const modifier of ['altKey', 'ctrlKey', 'metaKey']) {
      for (const shiftKey of [false, true]) {
        assert.equal(keyboardFloorMove(positions, 'T1', key, shiftKey, { [modifier]: true }), null);
      }
    }
  }
  assert.deepEqual(positions.T1, { x: 50, y: 50 });
});

test('unmodified and Shift+Arrow demo movement remain available', () => {
  const positions = { T1: { x: 50, y: 50 }, T2: { x: 80, y: 80 } };
  assert.deepEqual(keyboardFloorMove(positions, 'T1', 'ArrowRight').positions.T1, { x: 52, y: 50 });
  assert.deepEqual(keyboardFloorMove(positions, 'T1', 'ArrowRight', true).positions.T1, { x: 60, y: 50 });
});

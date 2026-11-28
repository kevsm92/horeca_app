import test from 'node:test';
import assert from 'node:assert/strict';
import { keyboardFloorMove } from '../src/floorKeyboardMove.js';

// Synthetic keyboard UI only; no server-side table seating or authorization logic.
test('non-arrow and inherited property names cannot move a demo table', () => {
  const positions = Object.freeze({ T1: Object.freeze({ x: 50, y: 50 }) });
  for (const key of ['Enter', 'Escape', 'Tab', 'Home', 'PageDown', 'arrowright', '__proto__', 'constructor', null]) {
    assert.equal(keyboardFloorMove(positions, 'T1', key), null);
  }
  for (const id of ['T2', '__proto__', 'constructor', 'toString']) {
    assert.equal(keyboardFloorMove(positions, id, 'ArrowRight'), null);
  }
  assert.deepEqual(positions.T1, { x: 50, y: 50 });
});

test('invalid or missing visual coordinates fail closed without exceptions', () => {
  for (const positions of [null, undefined, {}, { T1: null }, { T1: { x: NaN, y: 50 } }, { T1: { x: 50, y: Infinity } }]) {
    assert.equal(keyboardFloorMove(positions, 'T1', 'ArrowUp'), null);
  }
});

test('keyboard announcements distinguish successful small/large steps and boundary rejection', () => {
  const positions = Object.freeze({ T1: Object.freeze({ x: 80, y: 50 }) });
  const normal = keyboardFloorMove(positions, 'T1', 'ArrowLeft');
  assert.equal(normal.announcement, 'T1 moved left.');
  assert.deepEqual(normal.positions.T1, { x: 78, y: 50 });
  const large = keyboardFloorMove(positions, 'T1', 'ArrowLeft', true);
  assert.equal(large.announcement, 'T1 moved left (large step).');
  assert.deepEqual(large.positions.T1, { x: 70, y: 50 });
  const blocked = keyboardFloorMove({ T1: { x: 10, y: 50 } }, 'T1', 'ArrowLeft');
  assert.equal(blocked.announcement, 'T1 cannot move left: floor-plan boundary.');
  assert.deepEqual(blocked.positions.T1, { x: 10, y: 50 });
  assert.deepEqual(positions.T1, { x: 80, y: 50 });
});

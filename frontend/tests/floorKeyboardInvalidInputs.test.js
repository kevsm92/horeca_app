import test from 'node:test';
import assert from 'node:assert/strict';
import { keyboardFloorMove } from '../src/floorKeyboardMove.js';

// Synthetic keyboard navigation only; no seating decision or persistence.
test('non-arrow keys and unknown table IDs are ignored without changing geometry', () => {
  const positions = Object.freeze({ T1: Object.freeze({ x: 50, y: 50 }) });
  for (const key of ['Enter', 'Escape', 'Tab', ' ', 'ArrowDiagonal', '', null, undefined]) {
    assert.equal(keyboardFloorMove(positions, 'T1', key), null, String(key));
  }
  for (const id of ['T2', '__proto__', 'constructor', '', null, undefined]) {
    assert.equal(keyboardFloorMove(positions, id, 'ArrowRight'), null, String(id));
  }
  assert.deepEqual(positions, { T1: { x: 50, y: 50 } });
});

test('missing or invalid floor coordinates cannot trigger keyboard movement', () => {
  for (const positions of [
    null,
    undefined,
    {},
    { T1: null },
    { T1: { x: NaN, y: 50 } },
    { T1: { x: Infinity, y: 50 } },
    { T1: { x: 50, y: -Infinity } },
  ]) {
    assert.equal(keyboardFloorMove(positions, 'T1', 'ArrowLeft'), null);
  }
});

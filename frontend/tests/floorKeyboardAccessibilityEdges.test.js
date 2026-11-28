import test from 'node:test';
import assert from 'node:assert/strict';
import { keyboardFloorMove } from '../src/floorKeyboardMove.js';

// Synthetic visual layout only; this does not authorize or persist table moves.
const positions = Object.freeze({
  T1: Object.freeze({ x: 40, y: 40 }),
  T2: Object.freeze({ x: 80, y: 80 })
});

test('Shift+Arrow moves a larger step without changing the original layout', () => {
  const result = keyboardFloorMove(positions, 'T1', 'ArrowUp', true);
  assert.deepEqual(result.positions.T1, { x: 40, y: 30 });
  assert.equal(result.announcement, 'T1 moved up (large step).');
  assert.deepEqual(positions.T1, { x: 40, y: 40 });
  assert.equal(result.positions.T2, positions.T2);
});

test('browser and assistive technology modifiers are never intercepted', () => {
  for (const modifier of ['altKey', 'ctrlKey', 'metaKey']) {
    assert.equal(keyboardFloorMove(positions, 'T1', 'ArrowRight', false, { [modifier]: true }), null);
    assert.equal(keyboardFloorMove(positions, 'T1', 'ArrowRight', true, { [modifier]: true }), null);
  }
});

test('large keyboard steps respect the visual boundary and do not mutate layout', () => {
  const nearEdge = Object.freeze({ T1: Object.freeze({ x: 12, y: 40 }) });
  const result = keyboardFloorMove(nearEdge, 'T1', 'ArrowLeft', true);
  assert.equal(result.positions, nearEdge);
  assert.equal(result.announcement, 'T1 cannot move left: floor-plan boundary.');
});

test('invalid positions and inherited table identifiers cannot move', () => {
  assert.equal(keyboardFloorMove({ T1: { x: NaN, y: 40 } }, 'T1', 'ArrowUp'), null);
  assert.equal(keyboardFloorMove({}, 'toString', 'ArrowRight'), null);
});

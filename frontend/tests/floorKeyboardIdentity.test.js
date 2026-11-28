import test from 'node:test';
import assert from 'node:assert/strict';
import { keyboardFloorMove } from '../src/floorKeyboardMove.js';

test('keyboard moves only the selected synthetic table and preserves neighboring references', () => {
  const neighbor = Object.freeze({ x: 75, y: 75 });
  const selected = Object.freeze({ x: 40, y: 40 });
  const positions = Object.freeze({ T1: selected, T2: neighbor });
  const result = keyboardFloorMove(positions, 'T1', 'ArrowRight');
  assert.deepEqual(result.positions.T1, { x: 42, y: 40 });
  assert.equal(result.positions.T2, neighbor);
  assert.equal(positions.T1, selected);
  assert.equal(result.announcement, 'T1 moved right.');
});

test('unknown table IDs and inherited property names never move floor controls', () => {
  const positions = Object.freeze({ T1: Object.freeze({ x: 40, y: 40 }) });
  for (const id of ['T2', 'toString', '__proto__', 'constructor']) {
    assert.equal(keyboardFloorMove(positions, id, 'ArrowRight'), null);
  }
  assert.deepEqual(positions.T1, { x: 40, y: 40 });
});

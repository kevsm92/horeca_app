import test from 'node:test';
import assert from 'node:assert/strict';
import { keyboardFloorMove } from '../src/floorKeyboardMove.js';
import { initialFloorPositions } from '../src/floorLayout.js';

test('announces a successful keyboard move without mutating the input', () => {
  const result = keyboardFloorMove(initialFloorPositions, 'T1', 'ArrowLeft');
  assert.equal(result.announcement, 'T1 moved left.');
  assert.deepEqual(result.positions.T1, { x: 18, y: 20 });
  assert.deepEqual(initialFloorPositions.T1, { x: 20, y: 20 });
});

test('distinguishes boundary and neighboring table collision', () => {
  const boundary = { T1: { x: 10, y: 20 } };
  assert.equal(keyboardFloorMove(boundary, 'T1', 'ArrowLeft').announcement,
    'T1 cannot move left: floor-plan boundary.');
  const collision = { T1: { x: 20, y: 20 }, T2: { x: 33, y: 20 } };
  assert.equal(keyboardFloorMove(collision, 'T1', 'ArrowRight').announcement,
    'T1 cannot move right: another table is too close.');
});

test('ignores unrelated keys and unknown tables', () => {
  assert.equal(keyboardFloorMove(initialFloorPositions, 'T1', 'Enter'), null);
  assert.equal(keyboardFloorMove(initialFloorPositions, 'missing', 'ArrowRight'), null);
});

test('preserves browser modifier shortcuts without moving or announcing', () => {
  for (const modifiers of [{altKey:true},{ctrlKey:true},{metaKey:true}]) {
    assert.equal(keyboardFloorMove(initialFloorPositions, 'T1', 'ArrowRight', false, modifiers), null);
  }
  assert.equal(keyboardFloorMove(initialFloorPositions, 'T1', 'ArrowRight', false, {altKey:false,ctrlKey:false,metaKey:false}).announcement, 'T1 moved right.');
});

test('Shift+arrow uses larger steps and reports blocked movement without mutation', () => {
  const positions = { T1: {x:20,y:20} };
  const moved = keyboardFloorMove(positions, 'T1', 'ArrowDown', true);
  assert.deepEqual(moved.positions.T1, {x:20,y:30});
  assert.equal(moved.announcement, 'T1 moved down (large step).');
  assert.deepEqual(positions.T1, {x:20,y:20});
  const blocked = keyboardFloorMove({T1:{x:90,y:20}}, 'T1', 'ArrowRight', true);
  assert.equal(blocked.announcement, 'T1 cannot move right: floor-plan boundary.');
});

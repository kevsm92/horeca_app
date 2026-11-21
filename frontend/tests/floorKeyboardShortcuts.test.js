import test from 'node:test';
import assert from 'node:assert/strict';
import { keyboardFloorMove } from '../src/floorKeyboardMove.js';

// Synthetic floor geometry only; this does not validate real seating or venue permissions.
const positions = Object.freeze({
  T1: Object.freeze({x:20,y:20}),
  T2: Object.freeze({x:49,y:20})
});

test('modified and non-arrow shortcuts remain available to browsers and assistive technology', () => {
  for (const modifiers of [{altKey:true},{ctrlKey:true},{metaKey:true},{shiftKey:true,ctrlKey:true}]) {
    assert.equal(keyboardFloorMove(positions,'T1','ArrowRight',true,modifiers),null);
  }
  for (const key of ['Tab','Enter','Escape','Home','PageDown','__proto__','constructor']) {
    assert.equal(keyboardFloorMove(positions,'T1',key),null);
  }
  assert.equal(keyboardFloorMove(positions,'unknown','ArrowRight'),null);
});

test('arrow keys use small and Shift-large steps with distinct accessible announcements', () => {
  const small = keyboardFloorMove(positions,'T1','ArrowRight');
  const large = keyboardFloorMove(positions,'T1','ArrowDown',true);
  assert.deepEqual(small.positions.T1,{x:22,y:20});
  assert.deepEqual(large.positions.T1,{x:20,y:30});
  assert.equal(small.announcement,'T1 moved right.');
  assert.equal(large.announcement,'T1 moved down (large step).');
  assert.strictEqual(small.positions.T2,positions.T2);
  assert.deepEqual(positions.T1,{x:20,y:20});
});

test('blocked movement preserves state and announces floor boundary or collision', () => {
  const edge = Object.freeze({T1:Object.freeze({x:10,y:10})});
  const boundary = keyboardFloorMove(edge,'T1','ArrowUp');
  assert.strictEqual(boundary.positions,edge);
  assert.match(boundary.announcement,/floor-plan boundary/);
  const close = Object.freeze({T1:Object.freeze({x:20,y:20}),T2:Object.freeze({x:33,y:20})});
  const collision = keyboardFloorMove(close,'T1','ArrowRight');
  assert.strictEqual(collision.positions,close);
  assert.match(collision.announcement,/another table is too close/);
});

import test from 'node:test';
import assert from 'node:assert/strict';
import {pointerFloorPosition} from '../src/pointerFloorPosition.js';
import {initialFloorPositions, moveTable} from '../src/floorLayout.js';

// Synthetic visual geometry only: no table occupancy, capacity or Python state changes.
test('pointer drag beyond the room clamps visual position without moving other tables', () => {
  const start = Object.freeze({x:100,y:100});
  const current = Object.freeze({x:2000,y:-2000});
  const bounds = Object.freeze({width:500,height:300});
  const origin = Object.freeze({...initialFloorPositions.T1});
  const point = pointerFloorPosition(origin,start,current,bounds);
  const moved = moveTable(initialFloorPositions,'T1',point.x,point.y);
  assert.deepEqual(moved.T1,{x:90,y:10});
  assert.deepEqual(initialFloorPositions.T1,{x:20,y:20});
  assert.equal(moved.T2,initialFloorPositions.T2);
  assert.deepEqual(start,{x:100,y:100});
  assert.deepEqual(current,{x:2000,y:-2000});
});

test('zero pointer displacement retains identical layout reference', () => {
  const origin = initialFloorPositions.T3;
  const point = pointerFloorPosition(origin,{x:15,y:20},{x:15,y:20},{width:300,height:400});
  assert.equal(moveTable(initialFloorPositions,'T3',point.x,point.y),initialFloorPositions);
});

test('invalid pointer geometry is ignored instead of corrupting layout', () => {
  const point = pointerFloorPosition(initialFloorPositions.T1,{x:0,y:0},{x:10,y:10},{width:0,height:200});
  assert.equal(point,null);
  assert.equal(moveTable(initialFloorPositions,'T1',point?.x,point?.y),initialFloorPositions);
});

test('same proportional pointer drag behaves consistently across responsive floor dimensions', () => {
  for (const [width, height] of [[300, 200], [900, 600], [1200, 400]]) {
    const positions = Object.freeze({ T1: Object.freeze({ x: 25, y: 35 }), T2: Object.freeze({ x: 75, y: 75 }) });
    const point = pointerFloorPosition(positions.T1, { x: 50, y: 60 },
      { x: 50 + width * 0.15, y: 60 + height * 0.1 }, { width, height });
    const next = moveTable(positions, 'T1', point.x, point.y);
    assert.notEqual(next, positions);
    assert.ok(Math.abs(next.T1.x - 40) < 1e-10);
    assert.ok(Math.abs(next.T1.y - 45) < 1e-10);
    assert.equal(next.T2, positions.T2);
    assert.deepEqual(positions.T1, { x: 25, y: 35 });
  }
});

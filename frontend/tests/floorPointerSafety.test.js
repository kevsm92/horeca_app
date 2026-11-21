import test from 'node:test';
import assert from 'node:assert/strict';
import {pointerFloorPosition} from '../src/pointerFloorPosition.js';

// Synthetic pointer geometry only; these checks do not authorize venue layout writes.
test('pointer geometry is independent of absolute viewport offset and does not mutate inputs', () => {
  const origin = Object.freeze({x:30,y:40});
  const start = Object.freeze({x:250,y:300});
  const current = Object.freeze({x:300,y:330});
  const bounds = Object.freeze({width:500,height:300});
  assert.deepEqual(pointerFloorPosition(origin,start,current,bounds),{x:40,y:50});
  assert.deepEqual(pointerFloorPosition(origin,{x:0,y:0},{x:50,y:30},bounds),{x:40,y:50});
  assert.deepEqual(origin,{x:30,y:40});
  assert.deepEqual(start,{x:250,y:300});
  assert.deepEqual(current,{x:300,y:330});
  assert.deepEqual(bounds,{width:500,height:300});
});

test('nonfinite coordinates and nonpositive room dimensions fail closed', () => {
  const origin = {x:20,y:20};
  const start = {x:0,y:0};
  const current = {x:10,y:10};
  const bounds = {width:100,height:100};
  assert.equal(pointerFloorPosition({...origin,x:Infinity},start,current,bounds),null);
  assert.equal(pointerFloorPosition(origin,start,{...current,y:NaN},bounds),null);
  assert.equal(pointerFloorPosition(origin,start,current,{...bounds,height:-1}),null);
  assert.equal(pointerFloorPosition(origin,start,current,{...bounds,width:0}),null);
  assert.equal(pointerFloorPosition(origin,start,current,null),null);
});

test('extreme finite pointer deltas that overflow arithmetic are rejected', () => {
  const point = pointerFloorPosition(
    {x:20,y:20},
    {x:-Number.MAX_VALUE,y:0},
    {x:Number.MAX_VALUE,y:1},
    {width:1,height:100}
  );
  assert.equal(point,null);
});

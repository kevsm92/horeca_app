import test from 'node:test';
import assert from 'node:assert/strict';
import {initialFloorPositions,moveTable} from '../src/floorLayout.js';

test('synthetic floor movement rejects overlapping table centers without mutation',()=>{
  const before=structuredClone(initialFloorPositions);
  assert.equal(moveTable(initialFloorPositions,'T1',49,20),initialFloorPositions);
  assert.equal(moveTable(initialFloorPositions,'T1',38,20),initialFloorPositions);
  assert.deepEqual(initialFloorPositions,before);
});

test('demo table can still move alongside another table and to valid boundaries',()=>{
  const next=moveTable(initialFloorPositions,'T1',49,35);
  assert.notEqual(next,initialFloorPositions);
  assert.deepEqual(next.T1,{x:49,y:35});
  assert.deepEqual(moveTable(initialFloorPositions,'T1',-100,500).T1,{x:10,y:90});
});

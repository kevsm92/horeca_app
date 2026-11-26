import test from 'node:test';
import assert from 'node:assert/strict';
import {initialFloorPositions,moveTable} from '../src/floorLayout.js';

test('demo floor rejects overlapping table centers without changing the layout',()=>{
  const frozen=Object.freeze(Object.fromEntries(Object.entries(initialFloorPositions).map(([id,point])=>[id,Object.freeze({...point})])));
  const nearNeighbor=moveTable(frozen,'T1',initialFloorPositions.T2.x-5,initialFloorPositions.T2.y);
  assert.strictEqual(nearNeighbor,frozen);
  assert.deepEqual(frozen.T1,{x:20,y:20});
  const valid=moveTable(frozen,'T1',12,12);
  assert.notStrictEqual(valid,frozen);
  assert.deepEqual(valid.T1,{x:12,y:12});
  assert.strictEqual(valid.T2,frozen.T2);
});

test('collision guard requires proximity on both axes, not either axis alone',()=>{
  const positions=Object.freeze({T1:Object.freeze({x:20,y:20}),T2:Object.freeze({x:30,y:60})});
  const moved=moveTable(positions,'T1',30,30);
  assert.deepEqual(moved.T1,{x:30,y:30});
  assert.deepEqual(positions.T1,{x:20,y:20});
});

test('invalid floor coordinates and malformed points do not corrupt visual state',()=>{
  const positions={T1:{x:20,y:20},T2:{x:40,y:40}};
  for(const [x,y] of [[undefined,20],[20,null],[Infinity,20],[20,NaN]]) {
    assert.strictEqual(moveTable(positions,'T1',x,y),positions);
  }
  assert.strictEqual(moveTable({T1:{x:NaN,y:20}},'T1',30,30).T1.x!==undefined,true);
  assert.strictEqual(moveTable(null,'T1',30,30),null);
});

import test from 'node:test';
import assert from 'node:assert/strict';
import {initialFloorPositions,moveTable} from '../src/floorLayout.js';
test('all eight demo tables have finite distinct visual positions',()=>{assert.equal(Object.keys(initialFloorPositions).length,8);assert.equal(new Set(Object.values(initialFloorPositions).map(p=>p.x+','+p.y)).size,8);});
test('keyboard move produces immutable layout update',()=>{const moved=moveTable(initialFloorPositions,'T1',22,20);assert.equal(moved.T1.x,22);assert.equal(initialFloorPositions.T1.x,20);assert.equal(moved.T2,initialFloorPositions.T2);});
test('positions clamp within visual room bounds',()=>{const p=moveTable(initialFloorPositions,'T1',-50,500);assert.deepEqual(p.T1,{x:10,y:90});});
test('unknown table cannot be added by layout edit',()=>{assert.equal(moveTable(initialFloorPositions,'T99',50,50),initialFloorPositions);});
test('nonfinite coordinates are rejected',()=>{assert.equal(moveTable(initialFloorPositions,'T1',NaN,20),initialFloorPositions);assert.equal(moveTable(initialFloorPositions,'T1',20,Infinity),initialFloorPositions);});
test('no-op movement retains identity',()=>{assert.equal(moveTable(initialFloorPositions,'T1',20,20),initialFloorPositions);});

import test from 'node:test';
import assert from 'node:assert/strict';
import {initialDemoTasks,resetDemoTasks,toggleDemoTask} from '../src/demoTasks.js';

test('synthetic task reset restores defaults with independent records',()=>{
  const changed=toggleDemoTask(resetDemoTasks(),0);
  const restored=resetDemoTasks();
  assert.deepEqual(restored,initialDemoTasks);
  assert.equal(changed[0].done,true);
  assert.equal(restored[0].done,false);
  assert.notStrictEqual(restored[0],initialDemoTasks[0]);
  assert.notStrictEqual(restored,initialDemoTasks);
});

test('toggle is immutable and invalid indices leave checklist untouched',()=>{
  const frozen=Object.freeze(resetDemoTasks().map(task=>Object.freeze(task)));
  const toggled=toggleDemoTask(frozen,1);
  assert.equal(toggled[1].done,false);
  assert.equal(frozen[1].done,true);
  assert.strictEqual(toggled[0],frozen[0]);
  for(const index of [-1,3,1.5,NaN])assert.strictEqual(toggleDemoTask(frozen,index),frozen);
});

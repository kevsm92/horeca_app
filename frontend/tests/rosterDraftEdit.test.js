import test from 'node:test';
import assert from 'node:assert/strict';
import {createDemoShiftDraft,replaceDemoShiftDraft} from '../src/rosterDraft.js';
const people=[{id:'sofia',name:'Sofia'},{id:'mila',name:'Mila'}];
const input={personId:'sofia',date:'2026-11-27',start:'09:00',end:'17:00'};
test('edit replaces exactly one draft without mutating input',()=>{
 const a=createDemoShiftDraft(input,people),b=createDemoShiftDraft({...input,personId:'mila'},people);
 const original=[a,b],updated=replaceDemoShiftDraft(original,a.id,{...input,start:'22:00',end:'02:00'},people);
 assert.equal(original[0],a);assert.equal(updated.length,2);assert.equal(updated[1],b);
 assert.equal(updated[0].overnight,true);assert.equal(updated[0].start,'22:00');
 assert.equal(updated[0].source,'synthetic-draft');
});
test('editing to identical draft conflicts with another draft',()=>{
 const a=createDemoShiftDraft(input,people),b=createDemoShiftDraft({...input,start:'10:00'},people);
 assert.throws(()=>replaceDemoShiftDraft([a,b],a.id,{...input,start:'10:00'},people),/Identical draft/);
});
test('missing draft and invalid edits fail without altering original',()=>{
 const a=createDemoShiftDraft(input,people),drafts=[a];
 assert.throws(()=>replaceDemoShiftDraft(drafts,'missing',input,people),/no longer exists/);
 assert.throws(()=>replaceDemoShiftDraft(drafts,a.id,{...input,end:'09:00'},people),/distinct/);
 assert.equal(drafts[0],a);
});
test('unchanged edit is permitted and stays synthetic',()=>{
 const a=createDemoShiftDraft(input,people),next=replaceDemoShiftDraft([a],a.id,input,people);
 assert.deepEqual(next,[a]);
});

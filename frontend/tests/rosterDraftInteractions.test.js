import test from 'node:test';
import assert from 'node:assert/strict';
import {createDemoShiftDraft,replaceDemoShiftDraft} from '../src/rosterDraft.js';

const people=[{id:'sofia',name:'Sofia'},{id:'noah',name:'Noah'}];
const shift={personId:'sofia',date:'2026-11-27',start:'09:00',end:'17:00'};

test('editing an existing synthetic draft updates only the selected shift',()=>{
 const original=createDemoShiftDraft(shift,people);
 const other=createDemoShiftDraft({...shift,personId:'noah'},people);
 const drafts=[original,other];
 const updated=replaceDemoShiftDraft(drafts,original.id,{...shift,start:'10:00'},people);
 assert.equal(updated.length,2);
 assert.equal(updated[0].start,'10:00');
 assert.equal(updated[0].source,'synthetic-draft');
 assert.equal(updated[1],other);
 assert.deepEqual(drafts,[original,other]);
});
test('editing to an identical existing draft fails without mutating the list',()=>{
 const first=createDemoShiftDraft(shift,people);
 const second=createDemoShiftDraft({...shift,start:'10:00'},people);
 const drafts=[first,second];
 assert.throws(()=>replaceDemoShiftDraft(drafts,first.id,{...shift,start:'10:00'},people),/Identical draft/);
 assert.deepEqual(drafts,[first,second]);
});
test('editing a removed draft cannot recreate it',()=>{
 assert.throws(()=>replaceDemoShiftDraft([],'removed',shift,people),/no longer exists/);
});
test('duplicate action requires a changed date or time and preserves the original',()=>{
 const original=createDemoShiftDraft(shift,people);
 assert.throws(()=>createDemoShiftDraft({...original},people,[original]),/Identical draft/);
 const copy=createDemoShiftDraft({...original,date:'2026-11-28'},people,[original]);
 assert.notEqual(copy.id,original.id);
 assert.equal(copy.source,'synthetic-draft');
 assert.equal(original.date,'2026-11-27');
});
test('duplicating overnight shift retains the overnight label',()=>{
 const original=createDemoShiftDraft({...shift,start:'22:00',end:'02:00'},people);
 const copy=createDemoShiftDraft({...original,date:'2026-11-28'},people,[original]);
 assert.equal(copy.overnight,true);
});

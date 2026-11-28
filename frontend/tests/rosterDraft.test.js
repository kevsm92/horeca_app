import test from 'node:test';
import assert from 'node:assert/strict';
import {createDemoShiftDraft} from '../src/rosterDraft.js';
const staff=[{id:'sofia',name:'Sofia'}];
const valid={personId:'sofia',date:'2026-11-27',start:'09:00',end:'17:00'};
test('creates explicitly synthetic unsaved draft',()=>{
 const d=createDemoShiftDraft(valid,staff);
 assert.equal(d.source,'synthetic-draft');assert.equal(d.personName,'Sofia');assert.equal(d.overnight,false);
});
test('overnight drafts remain visibly flagged',()=>{
 assert.equal(createDemoShiftDraft({...valid,start:'22:00',end:'02:00'},staff).overnight,true);
});
test('invalid dates, times, employees and zero-duration drafts rejected',()=>{
 for(const changes of [{date:'2026-02-30'},{start:'25:00'},{end:'09:00',start:'09:00'},{personId:'unknown'}])
  assert.throws(()=>createDemoShiftDraft({...valid,...changes},staff),TypeError);
});
test('duplicate draft is rejected but distinct time remains possible',()=>{
 const first=createDemoShiftDraft(valid,staff);
 assert.throws(()=>createDemoShiftDraft(valid,staff,[first]),/Identical draft/);
 assert.doesNotThrow(()=>createDemoShiftDraft({...valid,start:'10:00'},staff,[first]));
});

// Lightweight source regression for the accessible week-scoped draft indicator.
test('weekly roster labels browser-only drafts for the selected week',async()=>{
 const {readFileSync}=await import('node:fs');
 const {fileURLToPath}=await import('node:url');
 const source=readFileSync(fileURLToPath(new URL('../src/WeeklySchedule.jsx',import.meta.url)),'utf8');
 assert.match(source,/const weekDrafts = drafts\.filter\(draft=>days\.some\(day=>day\.key===draft\.date\)\)/);
 assert.match(source,/role="status" aria-live="polite"[^>]*>\{weekDrafts\.length\} unsaved fictional/);
 assert.match(source,/this week · not published/);
});

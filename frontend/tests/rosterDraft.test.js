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

test('successful draft submission navigates to the draft week without publishing',async()=>{
 const {readFileSync}=await import('node:fs');
 const {fileURLToPath}=await import('node:url');
 const source=readFileSync(fileURLToPath(new URL('../src/WeeklySchedule.jsx',import.meta.url)),'utf8');
 assert.match(source,/chooseDate\(input\.date\);setView\('grid'\);setExpandedShift\(null\);setDraftError\(''\)/);
 assert.match(source,/setDraftNotice\('Fictional shift draft added in this browser only\. Nothing was published\.'\)/);
 assert.match(source,/setDraftNotice\('Fictional shift draft updated in this browser only\. Nothing was published\.'\)/);
});

test('daily agenda can duplicate an unsaved draft without publishing',async()=>{
 const {readFileSync}=await import('node:fs');
 const {fileURLToPath}=await import('node:url');
 const source=readFileSync(fileURLToPath(new URL('../src/WeeklySchedule.jsx',import.meta.url)),'utf8');
 assert.match(source,/Duplicate unsaved draft for /);
 assert.match(source,/from daily agenda/);
 assert.match(source,/setCopyDraft\(\{\.\.\.draft,id:"copy:"\+draft\.id\}\);setDraftOpen\(true\)/);
 assert.match(source,/Change the date or time before adding this duplicate draft\./);
});

test('weekly grid offers draft duplication with unpublished preview guidance',async()=>{
 const {readFileSync}=await import('node:fs');
 const {fileURLToPath}=await import('node:url');
 const source=readFileSync(fileURLToPath(new URL('../src/WeeklySchedule.jsx',import.meta.url)),'utf8');
 assert.match(source,/Duplicate unsaved draft for '\+draft\.personName\+' on '\+draft\.date\+' from weekly grid'/);
 assert.match(source,/setCopyDraft\(\{\.\.\.draft,id:'copy:'\+draft\.id\}\);setDraftOpen\(true\)/);
 assert.match(source,/Change the date or time before adding this duplicate draft\./);
 assert.match(source,/Local preview only — not published or saved to a server\./);
});

test('draft editor focuses its heading and offers cancellation for new as well as edited drafts',async()=>{
 const {readFileSync}=await import('node:fs');
 const {fileURLToPath}=await import('node:url');
 const source=readFileSync(fileURLToPath(new URL('../src/WeeklySchedule.jsx',import.meta.url)),'utf8');
 assert.match(source,/useEffect\(\(\)=>\{if\(draftOpen\)draftHeadingRef\.current\?\.focus\(\);\},\[draftOpen,editingDraftId,copyDraft\]\)/);
 assert.match(source,/<h3 ref=\{draftHeadingRef\} tabIndex=\{-1\}>/);
 assert.match(source,/<button type="button" onClick=\{\(\)=>\{setEditingDraftId\(null\);setCopyDraft\(null\);setDraftOpen\(false\);setDraftError\(''\);\}\}>Cancel draft form<\/button>/);
});

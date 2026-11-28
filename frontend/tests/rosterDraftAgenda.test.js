import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createDemoShiftDraft} from '../src/rosterDraft.js';

const jsx=readFileSync(new URL('../src/WeeklySchedule.jsx',import.meta.url),'utf8');

test('daily agenda renders only drafts matching the selected calendar day',()=>{
  assert.match(jsx,/drafts\.filter\(draft=>draft\.date===day\.key\)\.map\(draft=>/);
  assert.match(jsx,/Unsaved fictional draft — not published/);
  assert.match(jsx,/draft\.overnight\?" \(\+1 day\)":""/);
});
test('empty daily agenda accounts for both scheduled shifts and drafts',()=>{
  assert.match(jsx,/!roster\.some\(person=>person\.shifts\[i\]\)&&!drafts\.some\(draft=>draft\.date===day\.key\)/);
});
test('draft dates are kept separate from published demo roster',()=>{
  const people=[{id:'test',name:'Fictional Test'}];
  const draft=createDemoShiftDraft({personId:'test',date:'2026-11-28',start:'22:00',end:'02:00'},people);
  assert.equal(draft.source,'synthetic-draft');
  assert.equal(draft.date,'2026-11-28');
  assert.equal(draft.overnight,true);
});

import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {demoRoster,weekDays,weekForDate} from '../src/demoRoster.js';
import {createDemoShiftDraft} from '../src/rosterDraft.js';

const source=readFileSync(new URL('../src/WeeklySchedule.jsx',import.meta.url),'utf8');

test('out-of-sample weeks can contain drafts without a fictional published roster',()=>{
  const date='2027-01-13';
  const week=weekForDate(date);
  const draft=createDemoShiftDraft({personId:'sofia',date,start:'09:00',end:'17:00'},[{id:'sofia',name:'Sofia'}]);
  assert.equal(demoRoster(week),null);
  assert.ok(weekDays(week).some(day=>day.key===draft.date));
});

test('draft-only grid explicitly warns that other staffing is unknown',()=>{
  assert.match(source,/!roster && view==='grid' && drafts\.some\(draft=>days\.some\(day=>day\.key===draft\.date\)\)/);
  assert.match(source,/Draft-only weekly preview: these are unsaved fictional shifts, not a published roster/);
  assert.match(source,/blank cells do not mean staff are off duty/);
  assert.match(source,/<p className="roster-empty" role="status">Draft-only weekly preview/);
});

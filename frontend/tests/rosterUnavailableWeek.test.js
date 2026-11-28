import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {demoRoster,weekForDate,weekDays} from '../src/demoRoster.js';

const jsx=readFileSync(new URL('../src/WeeklySchedule.jsx',import.meta.url),'utf8');

test('an out-of-sample draft date still resolves to a navigable calendar week',()=>{
  const date='2027-01-13';
  const week=weekForDate(date);
  assert.equal(demoRoster(week),null);
  assert.ok(weekDays(week).some(day=>day.key===date));
});

test('daily agenda renders without a sample roster and preserves drafts',()=>{
  assert.match(jsx,/\{view==='agenda' && <div/);
  assert.match(jsx,/drafts\.filter\(draft=>draft\.date===day\.key\)/);
  assert.match(jsx,/\(roster\|\|\[\]\)\.filter\(person=>person\.shifts\[i\]\)/);
  assert.match(jsx,/!drafts\.some\(draft=>draft\.date===day\.key\)/);
});

test('unknown staffing is not presented as an off-duty or published schedule',()=>{
  assert.match(jsx,/Actual staffing is unknown/);
  assert.match(jsx,/Unsaved fictional draft — not published/);
});

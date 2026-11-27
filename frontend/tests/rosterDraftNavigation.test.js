import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {weekForDate} from '../src/demoRoster.js';

const component=readFileSync(new URL('../src/WeeklySchedule.jsx',import.meta.url),'utf8');

test('draft list provides a keyboard-operable View day action using calendar selection',()=>{
  assert.match(component,/aria-label=\{'View daily agenda for '\+draft\.personName\+' on '\+draft\.date\}/);
  assert.match(component,/onClick=\{\(\)=>\{chooseDate\(draft\.date\);setView\('agenda'\);\}\}>View day<\/button>/);
});
test('draft navigation uses the same Monday-based calendar week as the agenda',()=>{
  assert.equal(weekForDate('2026-11-27'),'2026-11-23');
  assert.equal(weekForDate('2026-11-30'),'2026-11-30');
  assert.equal(weekForDate('2026-12-06'),'2026-11-30');
});

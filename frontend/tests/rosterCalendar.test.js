import test from 'node:test';
import assert from 'node:assert/strict';
import {weekForDate,weekDays} from '../src/demoRoster.js';
test('calendar picks Monday of selected week across month and year boundaries',()=>{
  assert.equal(weekForDate('2026-11-26'),'2026-11-23');
  assert.equal(weekForDate('2026-11-29'),'2026-11-23');
  assert.equal(weekForDate('2027-01-01'),'2026-12-28');
  assert.equal(weekForDate('2027-01-04'),'2027-01-04');
});
test('reject invalid dates rather than silently rolling them forward',()=>{
  for(const value of ['2026-02-30','2026-13-01','2026-11-2','hello',null])assert.throws(()=>weekForDate(value),TypeError);
});
test('chosen week always begins on Monday and contains seven distinct days',()=>{
  for(const date of ['2026-11-26','2027-01-01','2028-02-29']){
    const days=weekDays(weekForDate(date));
    assert.equal(days.length,7);
    assert.equal(days[0].day,'Mon');
    assert.equal(new Set(days.map(d=>d.key)).size,7);
    assert.ok(days.some(d=>d.key===date));
  }
});

import test from 'node:test';
import assert from 'node:assert/strict';
import {DEMO_WEEK,shiftWeek,weekDays,demoRoster} from '../src/demoRoster.js';

test('week navigation handles month/year boundaries and returns seven consecutive dates',()=>{
  assert.equal(shiftWeek(DEMO_WEEK,1),'2026-11-30');
  assert.equal(shiftWeek('2026-12-28',1),'2027-01-04');
  assert.equal(shiftWeek('2026-03-30',-1),'2026-03-23');
  const days=weekDays('2026-12-28');
  assert.equal(days.length,7);
  assert.deepEqual(days.map(d=>d.key),['2026-12-28','2026-12-29','2026-12-30','2026-12-31','2027-01-01','2027-01-02','2027-01-03']);
});
test('roster preserves staff identity and explicitly distinguishes scheduled and off cells',()=>{
  const rows=demoRoster(DEMO_WEEK);
  assert.equal(new Set(rows.map(r=>r.id)).size,4);
  assert.ok(rows.every(r=>r.shifts.length===7&&r.shifts.filter(Boolean).length===5));
  assert.equal(rows[0].shifts[2],null);
  assert.equal(rows[0].shifts[0].time,'11:00–19:00');
  assert.ok(rows.flatMap(r=>r.shifts).filter(Boolean).every(s=>Object.keys(s).length===1));
});
test('second demo week is distinct and unknown weeks are not falsely marked off',()=>{
  const rows=demoRoster(shiftWeek(DEMO_WEEK,1));
  assert.ok(rows[2].shifts.some(s=>s?.time.includes('(+1 day)')));
  assert.notDeepEqual(rows,demoRoster(DEMO_WEEK));
  assert.equal(demoRoster(shiftWeek(DEMO_WEEK,-1)),null);
  assert.equal(demoRoster(shiftWeek(DEMO_WEEK,2)),null);
});
test('changing returned roster cannot mutate future snapshots',()=>{
  const rows=demoRoster(DEMO_WEEK);
  rows[0].shifts[0].time='invalid'; rows[0].name='changed';
  assert.equal(demoRoster(DEMO_WEEK)[0].shifts[0].time,'11:00–19:00');
  assert.equal(demoRoster(DEMO_WEEK)[0].name,'Sofia');
});

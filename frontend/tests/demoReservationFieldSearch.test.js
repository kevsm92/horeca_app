import test from 'node:test';
import assert from 'node:assert/strict';
import {filterDemoReservations} from '../src/demoReservations.js';

// Synthetic search is presentation-only; results must not imply availability.
const records = Object.freeze([
  Object.freeze({id:'r1',name:'Anaïs O’Neil',table:'T1',time:'19:30',guests:2}),
  Object.freeze({id:'r2',name:'Anais Oliver',table:'T10',time:'20:00',guests:4}),
  Object.freeze({id:'r3',name:'Jules Martin',table:'T2',time:'19:30',guests:2})
]);

test('search terms can match different display fields without altering frozen records', () => {
  const matches=filterDemoReservations(records,'ANAIS 19:30 T1');
  assert.deepEqual(matches.map(row=>row.id),['r1']);
  assert.strictEqual(matches[0],records[0]);
  assert.deepEqual(filterDemoReservations(records,'20 00 anais').map(row=>row.id),['r2']);
  assert.deepEqual(records.map(row=>row.table),['T1','T10','T2']);
});

test('blank query returns a separate ordered array, not an editable source reference', () => {
  const matches=filterDemoReservations(records,'  — /  ');
  assert.notStrictEqual(matches,records);
  assert.deepEqual(matches,records);
  matches.pop();
  assert.equal(records.length,3);
  assert.deepEqual(filterDemoReservations(records,'not present'),[]);
});

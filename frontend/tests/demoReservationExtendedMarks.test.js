import test from 'node:test';
import assert from 'node:assert/strict';
import {filterDemoReservations} from '../src/demoReservations.js';

// U+1AB0 is an extended combining mark outside the legacy U+0300–U+036F range.
// These are fictional guest names, not live Python reservation records.
const rows = Object.freeze([
  Object.freeze({id:'demo-1',name:'A\u1AB0lex Morgan',table:'T1',time:'19:00'}),
  Object.freeze({id:'demo-2',name:'José García',table:'T2',time:'20:00'})
]);

test('synthetic reservation search strips extended Unicode combining marks', () => {
  assert.deepEqual(filterDemoReservations(rows,'alex t1'), [rows[0]]);
  assert.deepEqual(filterDemoReservations(rows,'A\u1AB0LEX'), [rows[0]]);
  assert.deepEqual(filterDemoReservations(rows,'jose'), [rows[1]]);
});

test('extended-mark normalization does not mutate or reorder reservations', () => {
  const before=JSON.stringify(rows);
  assert.deepEqual(filterDemoReservations(rows,''), [...rows]);
  assert.deepEqual(filterDemoReservations(rows,'absent'), []);
  assert.equal(JSON.stringify(rows),before);
});

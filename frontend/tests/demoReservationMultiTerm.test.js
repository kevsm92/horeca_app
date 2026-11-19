import test from 'node:test';
import assert from 'node:assert/strict';
import {demoReservations, filterDemoReservations} from '../src/demoReservations.js';

const rows = Object.freeze([
  Object.freeze({id:'demo-a', name:'José García', table:'T2', time:'18:30'}),
  Object.freeze({id:'demo-b', name:'Zoë Martin', table:'T4', time:'19:15'}),
  Object.freeze({id:'demo-c', name:'Cafe\u0301 Group', table:'T6', time:'20:00'})
]);

test('multi-word queries match guest and table or time without reordering', () => {
  assert.deepEqual(filterDemoReservations(rows, 'JOSE   t2'), [rows[0]]);
  assert.deepEqual(filterDemoReservations(rows, '19:15\tzoe'), [rows[1]]);
  assert.deepEqual(filterDemoReservations(rows, 't6\n cafe'), [rows[2]]);
  assert.deepEqual(filterDemoReservations(rows, 't4 18:30'), []);
});

test('unicode whitespace and accents are normalized without mutating source', () => {
  const before = JSON.stringify(rows);
  assert.deepEqual(filterDemoReservations(rows, '  zoe\u00a0 martin  '), [rows[1]]);
  assert.deepEqual(filterDemoReservations(rows, 'café\tgroup'), [rows[2]]);
  assert.deepEqual(filterDemoReservations(rows, '\u00a0\t'), rows);
  assert.notStrictEqual(filterDemoReservations(rows, ''), rows);
  assert.equal(JSON.stringify(rows), before);
});

test('existing single-field searches and synthetic records remain supported', () => {
  assert.deepEqual(filterDemoReservations(demoReservations, 'alex'), [demoReservations[0]]);
  assert.deepEqual(filterDemoReservations(demoReservations, 't3'), [demoReservations[1]]);
  assert.deepEqual(filterDemoReservations(demoReservations, '20:00'), [demoReservations[1]]);
});

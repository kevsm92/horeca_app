import test from 'node:test';
import assert from 'node:assert/strict';
import {filterDemoReservations} from '../src/demoReservations.js';

// Synthetic records only: this search does not query or modify Python reservations.
const reservations = Object.freeze([
  Object.freeze({id:'demo-accent-1', name:'José García', table:'T2', time:'18:30', guests:2}),
  Object.freeze({id:'demo-accent-2', name:'Zoë Martin', table:'T4', time:'19:15', guests:4}),
  Object.freeze({id:'demo-accent-3', name:'Cafe\u0301 Group', table:'T6', time:'20:00', guests:3})
]);

test('synthetic reservation search ignores accents and case in guest names', () => {
  assert.deepEqual(filterDemoReservations(reservations, ' JOSE GARCIA '), [reservations[0]]);
  assert.deepEqual(filterDemoReservations(reservations, 'ZOE'), [reservations[1]]);
  assert.deepEqual(filterDemoReservations(reservations, 'CAFÉ'), [reservations[2]]);
});

test('accent search preserves source records and supports table/time lookup', () => {
  const before = JSON.stringify(reservations);
  assert.deepEqual(filterDemoReservations(reservations, 't4'), [reservations[1]]);
  assert.deepEqual(filterDemoReservations(reservations, '20:00'), [reservations[2]]);
  assert.deepEqual(filterDemoReservations(reservations, 'nonexistent'), []);
  assert.equal(JSON.stringify(reservations), before);
});

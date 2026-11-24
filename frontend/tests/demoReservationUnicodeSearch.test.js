import test from 'node:test';
import assert from 'node:assert/strict';
import { filterDemoReservations } from '../src/demoReservations.js';

// Synthetic search behavior only; never a real reservation or availability lookup.
const reservations = Object.freeze([
  Object.freeze({ id: 'r1', name: 'Zoë D’Arcy', time: '19:30', table: 'T2', guests: 2 }),
  Object.freeze({ id: 'r2', name: 'José Núñez', time: '20:00', table: 'T4', guests: 4 })
]);

test('demo reservation search tolerates accents, punctuation and case', () => {
  assert.deepEqual(filterDemoReservations(reservations, 'ZOE D ARCY').map(r => r.id), ['r1']);
  assert.deepEqual(filterDemoReservations(reservations, 'jose nunez').map(r => r.id), ['r2']);
  assert.deepEqual(filterDemoReservations(reservations, '19:30').map(r => r.id), ['r1']);
});

test('search terms may match across guest, table and time without mutating data', () => {
  assert.deepEqual(filterDemoReservations(reservations, 't4 20:00 JOSE').map(r => r.id), ['r2']);
  assert.deepEqual(filterDemoReservations(reservations, 'T2 20:00'), []);
  assert.equal(filterDemoReservations(reservations, '   ').length, 2);
  assert.equal(reservations[0].name, 'Zoë D’Arcy');
});

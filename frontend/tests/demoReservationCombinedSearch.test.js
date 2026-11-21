import test from 'node:test';
import assert from 'node:assert/strict';
import { filterDemoReservations } from '../src/demoReservations.js';

// Synthetic bookings only. These filters do not establish real availability or venue access.
const bookings = Object.freeze([
  Object.freeze({ id: 'demo-a', name: 'Élodie Van Dijk', time: '18:30', table: 'T2', guests: 2 }),
  Object.freeze({ id: 'demo-b', name: 'Elodie Martin', time: '19:00', table: 'T4', guests: 4 }),
  Object.freeze({ id: 'demo-c', name: 'Jamie Lee', time: '18:30', table: 'T4', guests: 3 })
]);

test('reservation search combines guest, table and time terms without crossing bookings', () => {
  assert.deepEqual(filterDemoReservations(bookings, '  T2   ELODIE  18:30 ').map(r => r.id), ['demo-a']);
  assert.deepEqual(filterDemoReservations(bookings, 'Elodie T4 18:30'), []);
  assert.deepEqual(filterDemoReservations(bookings, '18:30 T4').map(r => r.id), ['demo-c']);
});

test('reservation search handles accents, combining marks and source immutability', () => {
  const before = JSON.stringify(bookings);
  assert.deepEqual(filterDemoReservations(bookings, 'e\u0301lodie van').map(r => r.id), ['demo-a']);
  assert.deepEqual(filterDemoReservations(bookings, 'ÉLODIE').map(r => r.id), ['demo-a', 'demo-b']);
  assert.deepEqual(filterDemoReservations(bookings, '   '), [...bookings]);
  assert.notStrictEqual(filterDemoReservations(bookings, ''), bookings);
  assert.equal(JSON.stringify(bookings), before);
});

import test from 'node:test';
import assert from 'node:assert/strict';
import {filterDemoReservations} from '../src/demoReservations.js';

// Fictional records only. Search does not determine actual reservation availability.
const reservations = Object.freeze([
  Object.freeze({id: 'demo-a', name: 'Élodie Martin', table: 'T2', time: '19:30'}),
  Object.freeze({id: 'demo-b', name: 'Elodie Martin', table: 'T3', time: '20:00'}),
  Object.freeze({id: 'demo-c', name: 'Alex Morgan', table: 'T2', time: '20:00'})
]);

test('synthetic reservation search matches independent terms across name, table and time', () => {
  assert.deepEqual(filterDemoReservations(reservations, '  ELODIE   t2  19:30 ').map(r => r.id), ['demo-a']);
  assert.deepEqual(filterDemoReservations(reservations, 'martin 20:00').map(r => r.id), ['demo-b']);
  assert.deepEqual(filterDemoReservations(reservations, 'T2 20:00').map(r => r.id), ['demo-c']);
  assert.deepEqual(filterDemoReservations(reservations, 'martin t9'), []);
});

test('blank search returns a new list without mutating synthetic reservation records', () => {
  const blank = filterDemoReservations(reservations, '  ');
  assert.notEqual(blank, reservations);
  assert.deepEqual(blank, reservations);
  blank.pop();
  assert.equal(reservations.length, 3);
  assert.equal(reservations[0].name, 'Élodie Martin');
});

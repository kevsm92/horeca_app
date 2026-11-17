import test from 'node:test';
import assert from 'node:assert/strict';
import { demoReservations, filterDemoReservations } from '../src/demoReservations.js';

test('demo reservations are clearly synthetic and immutable', () => {
  assert.equal(demoReservations.length, 2);
  assert.ok(demoReservations.every(row => row.id.startsWith('demo-') && Object.isFrozen(row)));
});
test('empty search returns a copy without changing source', () => {
  const result = filterDemoReservations(demoReservations, '  ');
  assert.deepEqual(result, demoReservations);
  assert.notStrictEqual(result, demoReservations);
});
test('search matches guest, table and time case-insensitively', () => {
  assert.equal(filterDemoReservations(demoReservations, ' alex ')[0].id, 'demo-r1');
  assert.equal(filterDemoReservations(demoReservations, 't3')[0].id, 'demo-r2');
  assert.equal(filterDemoReservations(demoReservations, '20:00')[0].id, 'demo-r2');
});
test('no matching reservations gives empty state without mutating input', () => {
  const before = JSON.stringify(demoReservations);
  assert.deepEqual(filterDemoReservations(demoReservations, 'not present'), []);
  assert.equal(JSON.stringify(demoReservations), before);
});

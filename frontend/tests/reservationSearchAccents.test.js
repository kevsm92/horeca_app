import test from 'node:test';
import assert from 'node:assert/strict';
import { demoReservations, filterDemoReservations } from '../src/demoReservations.js';

// Synthetic frontend filtering; not an availability or tenant-scope check.
test('search matches accented names without requiring accents in the query', () => {
  const rows = Object.freeze([{ id: 'demo-accent', name: 'Chloé Müller', table: 'T2', time: '18:30' }]);
  assert.deepEqual(filterDemoReservations(rows, 'chloe').map(r => r.id), ['demo-accent']);
  assert.deepEqual(filterDemoReservations(rows, 'MULLER').map(r => r.id), ['demo-accent']);
  assert.deepEqual(filterDemoReservations(rows, 'Chloé').map(r => r.id), ['demo-accent']);
});

test('search still matches table and time and preserves source data', () => {
  assert.deepEqual(filterDemoReservations(demoReservations, 't3').map(r => r.id), ['demo-r2']);
  assert.deepEqual(filterDemoReservations(demoReservations, '19:00').map(r => r.id), ['demo-r1']);
  assert.equal(Object.isFrozen(demoReservations), true);
  assert.notStrictEqual(filterDemoReservations(demoReservations, ''), demoReservations);
});

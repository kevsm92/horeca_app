import test from 'node:test';
import assert from 'node:assert/strict';
import { filterDemoReservations } from '../src/demoReservations.js';

const examples = Object.freeze([
  Object.freeze({ id: 'demo-unicode-1', name: 'Chloé Müller', table: 'T9', time: '18:30' }),
  Object.freeze({ id: 'demo-unicode-2', name: 'Zoë', table: 'T10', time: '19:30' })
]);

test('reservation demo search matches precomposed and decomposed accented names', () => {
  assert.deepEqual(filterDemoReservations(examples, 'CHLOE').map(row => row.id), ['demo-unicode-1']);
  assert.deepEqual(filterDemoReservations(examples, 'Mu\u0308ller').map(row => row.id), ['demo-unicode-1']);
  assert.deepEqual(filterDemoReservations(examples, 'ZOE').map(row => row.id), ['demo-unicode-2']);
});

test('reservation demo search preserves original names and order across repeated searches', () => {
  const snapshot = JSON.stringify(examples);
  assert.deepEqual(filterDemoReservations(examples, 't1').map(row => row.id), ['demo-unicode-2']);
  assert.deepEqual(filterDemoReservations(examples, '').map(row => row.id), ['demo-unicode-1', 'demo-unicode-2']);
  assert.equal(JSON.stringify(examples), snapshot);
});

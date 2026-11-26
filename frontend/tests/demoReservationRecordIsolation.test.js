import test from 'node:test';
import assert from 'node:assert/strict';
import { filterDemoReservations } from '../src/demoReservations.js';

// Presentation-only synthetic fixtures: never use these results as availability decisions.
const records = Object.freeze([
  Object.freeze({ id: 'demo-a', name: 'Sam Rivera', table: 'T2', time: '18:00' }),
  Object.freeze({ id: 'demo-b', name: 'Sam Rivera', table: 'T4', time: '20:30' }),
  Object.freeze({ id: 'demo-c', name: 'Riley Chen', table: 'T2', time: '20:30' })
]);

test('all search terms must match the same reservation, not different rows', () => {
  assert.deepEqual(filterDemoReservations(records, 'Sam T2 20:30'), []);
  assert.deepEqual(filterDemoReservations(records, 'Sam T4 20:30').map(row => row.id), ['demo-b']);
  assert.deepEqual(filterDemoReservations(records, 'Riley T2 20:30').map(row => row.id), ['demo-c']);
});

test('duplicate guest names retain distinct records, ordering and identity', () => {
  const result = filterDemoReservations(records, 'sam');
  assert.deepEqual(result.map(row => row.id), ['demo-a', 'demo-b']);
  assert.strictEqual(result[0], records[0]);
  assert.strictEqual(result[1], records[1]);
  result.reverse();
  assert.deepEqual(records.map(row => row.id), ['demo-a', 'demo-b', 'demo-c']);
});

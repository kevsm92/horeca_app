import test from 'node:test';
import assert from 'node:assert/strict';
import {filterDemoReservations} from '../src/demoReservations.js';

// Fictional guest records; this search does not verify a booking or a venue.
const records = Object.freeze([
  Object.freeze({id:'demo-a',name:'Anaïs O’Neil',table:'T1',time:'19:30'}),
  Object.freeze({id:'demo-b',name:"Anais O'Connor",table:'T2',time:'20:00'}),
  Object.freeze({id:'demo-c',name:'Anais Oliver',table:'T3',time:'20:30'})
]);

test('straight and curly apostrophes are interchangeable and optional in guest search', () => {
  for (const query of ["O'Neil", 'O’Neil', 'oneil', 'ANAIS ONEIL']) {
    assert.deepEqual(filterDemoReservations(records, query).map(row => row.id), ['demo-a']);
  }
  for (const query of ["O'Connor", 'O’Connor', 'oconnor']) {
    assert.deepEqual(filterDemoReservations(records, query).map(row => row.id), ['demo-b']);
  }
  assert.deepEqual(filterDemoReservations(records, 'anais oliver').map(row => row.id), ['demo-c']);
});

test('apostrophe normalization retains source identity and table/time filters', () => {
  const result = filterDemoReservations(records, 'oneil T1 19:30');
  assert.strictEqual(result[0], records[0]);
  assert.equal(result.length, 1);
  assert.deepEqual(filterDemoReservations(records, 'oneil T2'), []);
  assert.deepEqual(records.map(row => row.name), ['Anaïs O’Neil', "Anais O'Connor", 'Anais Oliver']);
});

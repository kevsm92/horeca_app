import test from 'node:test';
import assert from 'node:assert/strict';
import {filterDemoDishes} from '../src/demoDishSearch.js';

// Frontend-only synthetic menu: filtering must never reindex POS cart entries.
const dishes = Object.freeze([
  Object.freeze(['Fish & Chips', 1590, 'Mains']),
  Object.freeze(['Café-crème', 550, 'Drinks']),
  Object.freeze(['Fish Tacos', 1390, 'Mains']),
  Object.freeze(['Chips & Salsa', 690, 'Starters'])
]);

test('multiple search terms match regardless of word order and preserve cart indices', () => {
  assert.deepEqual(filterDemoDishes(dishes, 'All', 'chips fish'), [{dish:dishes[0],index:0}]);
  assert.deepEqual(filterDemoDishes(dishes, 'Mains', 'fish chips'), [{dish:dishes[0],index:0}]);
  assert.deepEqual(filterDemoDishes(dishes, 'Starters', 'fish chips'), []);
});

test('punctuation-only search behaves as an empty search and keeps category constraints', () => {
  assert.deepEqual(filterDemoDishes(dishes, 'Drinks', ' & -- !!! '), [{dish:dishes[1],index:1}]);
  assert.deepEqual(filterDemoDishes(dishes, 'All', '...').map(row=>row.index), [0,1,2,3]);
});

test('mixed diacritics and punctuation preserve source objects and original indices', () => {
  assert.deepEqual(filterDemoDishes(dishes, 'Drinks', 'CREME cafe'), [{dish:dishes[1],index:1}]);
  assert.equal(Object.isFrozen(dishes), true);
  assert.equal(Object.isFrozen(dishes[1]), true);
  assert.equal(dishes[1][0], 'Café-crème');
});

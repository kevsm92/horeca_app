import test from 'node:test';
import assert from 'node:assert/strict';
import {filterDemoDishes} from '../src/demoDishSearch.js';

// Presentation-only normalization of synthetic POS labels, not Python menu search.
const dishes = Object.freeze([
  Object.freeze(["Chef’s Special", 1900, 'Mains']),
  Object.freeze(["Chef's Salad", 1200, 'Starters']),
  Object.freeze(['Chefs Choice', 1700, 'Mains']),
  Object.freeze(['Café Creme', 450, 'Drinks'])
]);

test('curly and straight apostrophes match unpunctuated POS searches', () => {
  assert.deepEqual(filterDemoDishes(dishes, 'All', 'chefs').map(({index}) => index), [0, 1, 2]);
  assert.deepEqual(filterDemoDishes(dishes, 'Mains', "CHEF'S").map(({index}) => index), [0, 2]);
  assert.deepEqual(filterDemoDishes(dishes, 'Starters', 'chef’s salad').map(({index}) => index), [1]);
});

test('accent normalization and source identity survive punctuation searches', () => {
  const results = filterDemoDishes(dishes, 'Drinks', 'café crème');
  assert.deepEqual(results.map(({index}) => index), [3]);
  assert.strictEqual(results[0].dish, dishes[3]);
  assert.deepEqual(filterDemoDishes(dishes, 'All', 'chefs missing'), []);
});

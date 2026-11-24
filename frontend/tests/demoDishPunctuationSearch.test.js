import test from 'node:test';
import assert from 'node:assert/strict';
import {filterDemoDishes} from '../src/demoDishSearch.js';

// Synthetic frontend search only; the Python API owns real menu records and prices.
const dishes = Object.freeze([
  Object.freeze(['Fish & Chips', 1690, 'Mains']),
  Object.freeze(['Café-crème', 490, 'Drinks']),
  Object.freeze(['Chef’s Special: Tofu', 1990, 'Mains']),
]);

test('punctuation and symbols are equivalent to spaces in demo dish queries', () => {
  assert.deepEqual(filterDemoDishes(dishes, 'Mains', 'fish chips'), [{dish: dishes[0], index: 0}]);
  assert.deepEqual(filterDemoDishes(dishes, 'All', 'fish & chips'), [{dish: dishes[0], index: 0}]);
  assert.deepEqual(filterDemoDishes(dishes, 'Drinks', 'cafe creme'), [{dish: dishes[1], index: 1}]);
});

test('Unicode apostrophes and punctuation-separated query terms preserve original cart indices', () => {
  assert.deepEqual(filterDemoDishes(dishes, 'Mains', 'CHEF’S: TOFU'), [{dish: dishes[2], index: 2}]);
  assert.deepEqual(filterDemoDishes(dishes, 'Drinks', 'chef tofu'), []);
  assert.equal(dishes[2][0], 'Chef’s Special: Tofu');
});

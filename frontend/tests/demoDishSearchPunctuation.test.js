import test from 'node:test';
import assert from 'node:assert/strict';
import { filterDemoDishes } from '../src/demoDishSearch.js';

// Synthetic search only. Original indices are essential to the fictional POS cart.
test('punctuation and symbols normalize consistently without changing cart indices', () => {
  const dishes = Object.freeze([
    Object.freeze(['Fish & Chips', 1550, 'Mains']),
    Object.freeze(['Chef’s Special: Salmon', 2490, 'Mains']),
    Object.freeze(['Café-au-lait', 490, 'Drinks']),
    Object.freeze(['Fish Taco', 1100, 'Mains'])
  ]);
  assert.deepEqual(filterDemoDishes(dishes, 'Mains', 'chips fish'), [{dish: dishes[0], index: 0}]);
  assert.deepEqual(filterDemoDishes(dishes, 'Mains', 'chef s salmon'), [{dish: dishes[1], index: 1}]);
  assert.deepEqual(filterDemoDishes(dishes, 'Drinks', 'cafe au lait'), [{dish: dishes[2], index: 2}]);
  assert.deepEqual(filterDemoDishes(dishes, 'All', 'fish'), [
    {dish: dishes[0], index: 0}, {dish: dishes[3], index: 3}
  ]);
  assert.equal(dishes[0][0], 'Fish & Chips');
});

test('blank or punctuation-only queries retain category filtering and stable order', () => {
  const dishes = Object.freeze([
    Object.freeze(['Soup', 800, 'Starters']),
    Object.freeze(['Tea', 400, 'Drinks']),
    Object.freeze(['Salad', 950, 'Starters'])
  ]);
  const expected = [{dish: dishes[0], index: 0}, {dish: dishes[2], index: 2}];
  for (const query of ['', ' \t ', '!!!', '— / +']) {
    assert.deepEqual(filterDemoDishes(dishes, 'Starters', query), expected);
  }
});

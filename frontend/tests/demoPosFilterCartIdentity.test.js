import test from 'node:test';
import assert from 'node:assert/strict';
import {filterDemoDishes} from '../src/demoDishSearch.js';

// This tests fictional POS display identity only, not Python-owned pricing or orders.
const dishes = Object.freeze([
  Object.freeze(['Burrata', 1450, 'Starters']),
  Object.freeze(['Salmon', 2490, 'Mains']),
  Object.freeze(['Lemonade', 550, 'Drinks']),
  Object.freeze(['Risotto', 2150, 'Mains'])
]);

test('filter changes never renumber synthetic POS cart keys', () => {
  const cart = {3: 2};
  const mains = filterDemoDishes(dishes, 'Mains');
  assert.deepEqual(mains.map(({index}) => index), [1, 3]);
  const searched = filterDemoDishes(dishes, 'Mains', 'ris');
  assert.equal(searched[0].index, 3);
  assert.equal(searched[0].dish, dishes[3]);
  assert.equal(dishes[Number(Object.keys(cart)[0])][0], 'Risotto');
  assert.deepEqual(filterDemoDishes(dishes, 'Drinks').map(({index}) => index), [2]);
  assert.deepEqual(cart, {3: 2});
});

test('empty and unmatched filters preserve source references and order', () => {
  const before = JSON.stringify(dishes);
  const all = filterDemoDishes(dishes);
  assert.deepEqual(all.map(({index}) => index), [0, 1, 2, 3]);
  all.forEach(({dish}, index) => assert.equal(dish, dishes[index]));
  assert.deepEqual(filterDemoDishes(dishes, 'Mains', 'lemonade'), []);
  assert.equal(JSON.stringify(dishes), before);
});

import test from 'node:test';
import assert from 'node:assert/strict';
import {filterDemoDishes} from '../src/demoDishSearch.js';

// Fictional display data: duplicate names are not stable order/cart identifiers.
const dishes = Object.freeze([
  Object.freeze(['Espresso', 300, 'Drinks']),
  Object.freeze(['Espresso', 350, 'Specials']),
  Object.freeze(['Espresso', 300, 'Drinks']),
  Object.freeze(['Iced Tea', 450, 'Drinks'])
]);

test('duplicate synthetic menu labels retain distinct original cart indices', () => {
  const all = filterDemoDishes(dishes, 'All', 'espresso');
  assert.deepEqual(all.map(({index}) => index), [0, 1, 2]);
  all.forEach(({dish,index}) => assert.equal(dish, dishes[index]));
  assert.notEqual(all[0].dish, all[2].dish);
  assert.deepEqual(filterDemoDishes(dishes, 'Drinks', 'espresso').map(({index}) => index), [0, 2]);
  assert.deepEqual(filterDemoDishes(dishes, 'Specials', 'espresso').map(({index}) => index), [1]);
});

test('repeated filtering does not mutate duplicate-name source or synthetic cart', () => {
  const cart = Object.freeze({'2': 3});
  const snapshot = JSON.stringify(dishes);
  filterDemoDishes(dishes, 'Drinks', 'iced');
  filterDemoDishes(dishes, 'All', 'espresso');
  assert.equal(dishes[Number(Object.keys(cart)[0])], dishes[2]);
  assert.deepEqual(cart, {'2': 3});
  assert.equal(JSON.stringify(dishes), snapshot);
});

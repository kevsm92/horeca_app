import test from 'node:test';
import assert from 'node:assert/strict';
import {filterDemoDishes} from '../src/demoDishSearch.js';

// Synthetic catalog only: search results never authorize orders or set server prices.
const dishes = Object.freeze([
  Object.freeze(['Crème brûlée', 950, 'Desserts']),
  Object.freeze(['Café latte', 550, 'Drinks']), // combining acute accent
  Object.freeze(['Café mocha', 600, 'Drinks']),
  Object.freeze(['Crème brûlée', 1050, 'Specials'])
]);

test('fictional POS search normalizes composed and decomposed accents', () => {
  assert.deepEqual(filterDemoDishes(dishes, 'All', 'CREME BRULEE').map(x => x.index), [0, 3]);
  assert.deepEqual(filterDemoDishes(dishes, 'Drinks', 'cafe').map(x => x.index), [1, 2]);
  assert.deepEqual(filterDemoDishes(dishes, 'Drinks', 'café latte').map(x => x.index), [1]);
});

test('combined search and category preserve original identities without mutating catalog', () => {
  const before = JSON.stringify(dishes);
  assert.deepEqual(filterDemoDishes(dishes, 'Desserts', '  BRULEE   CREME ').map(x => x.index), [0]);
  assert.deepEqual(filterDemoDishes(dishes, 'Specials', 'creme brulee').map(x => x.index), [3]);
  assert.deepEqual(filterDemoDishes(dishes, 'Drinks', 'brulee'), []);
  assert.equal(JSON.stringify(dishes), before);
});

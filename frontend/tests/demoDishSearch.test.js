import test from 'node:test';
import assert from 'node:assert/strict';
import {filterDemoDishes} from '../src/demoDishSearch.js';
const dishes = Object.freeze([
  Object.freeze(['Seared Salmon', 2490, 'Mains']),
  Object.freeze(['House Lemonade', 550, 'Drinks']),
  Object.freeze(['Steak Frites', 2890, 'Mains'])
]);
test('search trims and ignores case while preserving original cart indices', () => {
  assert.deepEqual(filterDemoDishes(dishes, 'All', '  STEAK '), [{dish:dishes[2],index:2}]);
});
test('category and query compose without mutating the source', () => {
  assert.deepEqual(filterDemoDishes(dishes, 'Drinks', 'steak'), []);
  assert.deepEqual(filterDemoDishes(dishes, 'Mains', ''), [{dish:dishes[0],index:0},{dish:dishes[2],index:2}]);
  assert.equal(dishes.length,3);
});

test('accent-insensitive POS search handles composed and decomposed dish names', () => {
  const accented = Object.freeze([
    Object.freeze(['Crème brûlée', 850, 'Desserts']),
    Object.freeze(['Cafe\u0301 latte', 490, 'Drinks']),
    Object.freeze(['Salade niçoise', 1290, 'Mains'])
  ]);
  assert.deepEqual(filterDemoDishes(accented, 'Desserts', 'CREME BRULEE'), [{dish:accented[0],index:0}]);
  assert.deepEqual(filterDemoDishes(accented, 'All', 'café'), [{dish:accented[1],index:1}]);
  assert.deepEqual(filterDemoDishes(accented, 'Mains', 'NICOISE'), [{dish:accented[2],index:2}]);
});

test('synthetic POS search collapses Unicode whitespace without changing cart identities', () => {
  const catalog = Object.freeze([
    Object.freeze(['Crème\u00a0\u00a0brûlée', 850, 'Desserts']),
    Object.freeze(['Iced\n Coffee', 490, 'Drinks'])
  ]);
  assert.deepEqual(filterDemoDishes(catalog, 'Desserts', ' creme   brulee '), [{dish:catalog[0],index:0}]);
  assert.deepEqual(filterDemoDishes(catalog, 'Drinks', 'iced\tcoffee'), [{dish:catalog[1],index:1}]);
  assert.deepEqual(filterDemoDishes(catalog, 'Desserts', 'iced coffee'), []);
  assert.equal(catalog[0][0], 'Crème\u00a0\u00a0brûlée');
});

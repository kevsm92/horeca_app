import test from 'node:test';
import assert from 'node:assert/strict';
import {filterDemoDishes} from '../src/demoDishSearch.js';

const dishes = Object.freeze([
  Object.freeze(['Crème brûlée', 850, 'Desserts']),
  Object.freeze(['Iced Coffee', 490, 'Drinks']),
  Object.freeze(['Coffee Crème', 590, 'Drinks']),
  Object.freeze(['Crème caramel', 750, 'Desserts'])
]);

test('multi-term synthetic POS search matches any word order, accents and whitespace', () => {
  assert.deepEqual(filterDemoDishes(dishes, 'All', ' BRULEE   creme '), [{dish:dishes[0],index:0}]);
  assert.deepEqual(filterDemoDishes(dishes, 'Drinks', 'creme\tcoffee'), [{dish:dishes[2],index:2}]);
  assert.deepEqual(filterDemoDishes(dishes, 'Desserts', 'coffee creme'), []);
});

test('multi-term filtering preserves original cart indices, order and frozen catalog', () => {
  assert.deepEqual(filterDemoDishes(dishes, 'All', 'creme'), [{dish:dishes[0],index:0},{dish:dishes[2],index:2},{dish:dishes[3],index:3}]);
  assert.deepEqual(filterDemoDishes(dishes, 'All', '\u00a0 \t'), dishes.map((dish,index)=>({dish,index})));
  assert.equal(dishes[0][0], 'Crème brûlée');
});

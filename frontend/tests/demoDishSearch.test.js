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

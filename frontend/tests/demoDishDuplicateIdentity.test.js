import test from 'node:test';
import assert from 'node:assert/strict';
import {filterDemoDishes} from '../src/demoDishSearch.js';

// Synthetic POS search must retain source indices used by the in-memory demo cart.
// Matching labels are not unique identifiers; do not merge distinct menu rows.
const dishes=Object.freeze([
  Object.freeze(['House Lemonade',550,'Drinks']),
  Object.freeze(['Steak Frites',2890,'Mains']),
  Object.freeze(['House Lemonade',650,'Drinks']),
  Object.freeze(['House Lemonade',550,'Specials'])
]);

test('duplicate dish labels remain separate cart selections after filtering',()=>{
  const matches=filterDemoDishes(dishes,'Drinks','lemonade');
  assert.deepEqual(matches.map(({index})=>index),[0,2]);
  assert.strictEqual(matches[0].dish,dishes[0]);
  assert.strictEqual(matches[1].dish,dishes[2]);
  assert.notStrictEqual(matches[0].dish,matches[1].dish);
  assert.deepEqual(matches.map(({dish})=>dish[1]),[550,650]);
});

test('changing search and category does not renumber or mutate demo dishes',()=>{
  assert.deepEqual(filterDemoDishes(dishes,'All','house').map(({index})=>index),[0,2,3]);
  assert.deepEqual(filterDemoDishes(dishes,'Specials','house').map(({index})=>index),[3]);
  assert.deepEqual(filterDemoDishes(dishes,'Mains','steak').map(({index})=>index),[1]);
  assert.deepEqual(filterDemoDishes(dishes,'Drinks','no match'),[]);
  assert.deepEqual(dishes.map(d=>d[1]),[550,2890,650,550]);
});

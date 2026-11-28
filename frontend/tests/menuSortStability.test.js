import test from 'node:test';
import assert from 'node:assert/strict';
import {sortMenu} from '../src/menuViewModel.js';

// Sorting is browser presentation only; Python remains authoritative for prices and availability.
const items = Object.freeze([
  Object.freeze({id:'b',name:'Tea 10',priceCents:500}),
  Object.freeze({id:'a',name:'Tea 2',priceCents:500}),
  Object.freeze({id:'c',name:'Apple',priceCents:300}),
  Object.freeze({id:'d',name:'tea 2',priceCents:500})
]);

test('catalog sorting handles natural numbers and stable case-insensitive ties', () => {
  assert.deepEqual(sortMenu(items,'name').map(x=>x.id), ['c','a','d','b']);
  assert.deepEqual(sortMenu(items,'price-low').map(x=>x.id), ['c','b','a','d']);
  assert.deepEqual(sortMenu(items,'price-high').map(x=>x.id), ['b','a','d','c']);
});

test('catalog sorting never mutates or clones Python response records', () => {
  for(const order of ['default','name','price-low','price-high']){
    const sorted=sortMenu(items,order);
    assert.notStrictEqual(sorted,items);
    assert.ok(sorted.every(item=>items.includes(item)));
  }
  assert.deepEqual(items.map(x=>x.id), ['b','a','c','d']);
  assert.throws(()=>sortMenu(items,'unsupported'),TypeError);
});

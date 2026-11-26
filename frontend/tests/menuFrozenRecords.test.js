import test from 'node:test';
import assert from 'node:assert/strict';
import {filterMenu,sortMenu} from '../src/menuViewModel.js';

// Browser presentation only: never rewrite authoritative Python menu records.
const records=Object.freeze([
  Object.freeze({id:'a',kind:'food',name:'Café salad',description:'Seasonal herbs',available:true,priceCents:0}),
  Object.freeze({id:'b',kind:'drink',name:'Café latte',description:'Oat milk',available:false,priceCents:450}),
  Object.freeze({id:'c',kind:'food',name:'Soup',description:null,available:true,priceCents:1200})
]);

test('filtered and sorted catalog views preserve frozen Python records and original ordering',()=>{
  const matches=filterMenu(records,'cafe','all',false);
  assert.notStrictEqual(matches,records);
  assert.deepEqual(matches.map(item=>item.id),['a','b']);
  const sorted=sortMenu(matches,'price-high');
  assert.deepEqual(sorted.map(item=>item.id),['b','a']);
  assert.strictEqual(sorted[0],records[1]);
  assert.strictEqual(sorted[1],records[0]);
  assert.deepEqual(records.map(item=>item.id),['a','b','c']);
});

test('available-only filtering preserves source references even with an empty query',()=>{
  const filtered=filterMenu(records,'','all',true);
  assert.deepEqual(filtered.map(item=>item.id),['a','c']);
  assert.strictEqual(filtered[0],records[0]);
  assert.strictEqual(filtered[1],records[2]);
  assert.notStrictEqual(filtered,records);
  assert.deepEqual(filterMenu(records),records);
  assert.notStrictEqual(filterMenu(records),records);
});

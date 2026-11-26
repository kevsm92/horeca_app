import test from 'node:test';
import assert from 'node:assert/strict';
import {filterMenu} from '../src/menuViewModel.js';

// Read-only search presentation; Python remains authoritative for menu data and access.
const items=Object.freeze([
  Object.freeze({id:'a',kind:'food',name:'Crème brûlée',description:'Vanilla custard',available:true}),
  Object.freeze({id:'b',kind:'drink',name:'Chef’s café',description:'Oat-milk special',available:true}),
  Object.freeze({id:'c',kind:'food',name:'Tomato soup',description:'Fresh basil',available:false})
]);
const ids=rows=>rows.map(row=>row.id);

test('catalog search ignores accents, apostrophes, case and repeated whitespace',()=>{
  assert.deepEqual(ids(filterMenu(items,'CREME BRULEE')),['a']);
  assert.deepEqual(ids(filterMenu(items,'chefs cafe')),['b']);
  assert.deepEqual(ids(filterMenu(items,'  OAT   MILK ')),['b']);
  assert.deepEqual(ids(filterMenu(items,'vanilla creme')),['a']);
  assert.deepEqual(ids(filterMenu(items,'basil tomato')),['c']);
});

test('catalog search combines terms, type and availability without changing source records',()=>{
  assert.deepEqual(ids(filterMenu(items,'fresh tomato','food',true)),[]);
  assert.deepEqual(ids(filterMenu(items,'fresh tomato','food',false)),['c']);
  assert.deepEqual(ids(filterMenu(items,'cafe','food',false)),[]);
  assert.deepEqual(ids(filterMenu(items,'cafe','drink',true)),['b']);
  assert.deepEqual(ids(filterMenu(items,'   ')),['a','b','c']);
  assert.strictEqual(filterMenu(items,'creme')[0],items[0]);
  assert.deepEqual(ids(items),['a','b','c']);
});

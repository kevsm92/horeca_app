import test from 'node:test';
import assert from 'node:assert/strict';
import {filterMenu} from '../src/menuViewModel.js';

test('catalog search matches all words in any order without crossing item boundaries',()=>{
 const items=[
  {id:'one',kind:'food',name:'Crème brûlée'},
  {id:'two',kind:'food',name:'Crème caramel'},
  {id:'three',kind:'drink',name:'Iced Café crème'}
 ];
 assert.deepEqual(filterMenu(items,'brulee creme','food'),[items[0]]);
 assert.deepEqual(filterMenu(items,'CAFE  iced','drink'),[items[2]]);
 assert.deepEqual(filterMenu(items,'brulee caramel'),[]);
 assert.deepEqual(filterMenu(items,'creme','drink'),[items[2]]);
});

test('multi-term filtering preserves order, source objects, and whitespace normalization',()=>{
 const items=[
  Object.freeze({id:'a',kind:'food',name:'Lemon\u00a0 Tart'}),
  Object.freeze({id:'b',kind:'food',name:'Lemon Tart with Cream'}),
  Object.freeze({id:'c',kind:'drink',name:'Lemon Tea'})
 ];
 const frozen=Object.freeze(items);
 assert.deepEqual(filterMenu(frozen,' tart\t lemon ','food'),[items[0],items[1]]);
 assert.deepEqual(filterMenu(frozen,'   ','all'),items);
 assert.deepEqual(items.map(item=>item.id),['a','b','c']);
});

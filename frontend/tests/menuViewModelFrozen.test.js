import test from 'node:test';
import assert from 'node:assert/strict';
import {filterMenu,sortMenu} from '../src/menuViewModel.js';

const items=Object.freeze([
  Object.freeze({id:'a',kind:'food',name:'Crème brûlée',description:'Vanilla dessert',priceCents:900,available:true}),
  Object.freeze({id:'b',kind:'drink',name:'Café crème',description:null,priceCents:450,available:false}),
  Object.freeze({id:'c',kind:'food',name:'Creme brulee',description:'Classic',priceCents:900,available:true}),
  Object.freeze({id:'d',kind:'food',name:'Soup',description:'Crème fraîche',priceCents:700,available:true})
]);

test('authenticated catalog presentation filters frozen records without changing their identity or order',()=>{
  assert.deepEqual(filterMenu(items,'CREME', 'food',true).map(item=>item.id),['a','c','d']);
  assert.deepEqual(filterMenu(items,'brulee creme','food').map(item=>item.id),['a','c']);
  assert.deepEqual(filterMenu(items,'cafe','drink',true),[]);
  assert.deepEqual(filterMenu(items,'cafe','drink',false),[items[1]]);
  assert.deepEqual(filterMenu(items,'!!!').map(item=>item.id),['a','b','c','d']);
  assert.notStrictEqual(filterMenu(items,''),items);
  assert.ok(items.every(Object.isFrozen));
});

test('catalog display sorts are stable, non-mutating and do not alter Python prices',()=>{
  assert.deepEqual(sortMenu(items,'price-low').map(item=>item.id),['b','d','a','c']);
  assert.deepEqual(sortMenu(items,'price-high').map(item=>item.id),['a','c','d','b']);
  assert.deepEqual(sortMenu(items,'default'),items);
  assert.notStrictEqual(sortMenu(items,'default'),items);
  assert.deepEqual(items.map(item=>item.priceCents),[900,450,900,700]);
});

import test from 'node:test';
import assert from 'node:assert/strict';
import {filterMenu,sortMenu} from '../src/menuViewModel.js';

const catalog=Object.freeze([
 Object.freeze({id:'a',kind:'food',name:'Crème brûlée',description:'House dessert',available:true,priceCents:850}),
 Object.freeze({id:'b',kind:'drink',name:'Café crème',description:'Hot coffee',available:true,priceCents:450}),
 Object.freeze({id:'c',kind:'food',name:'Crème caramel',description:'House dessert',available:false,priceCents:600}),
 Object.freeze({id:'d',kind:'food',name:'Crème soup',description:'House starter',available:true,priceCents:600}),
 Object.freeze({id:'e',kind:'food',name:'Crème tart',description:'House dessert',available:true,priceCents:600})
]);

test('catalog filters compose with price ordering without changing Python records',()=>{
 const original=JSON.stringify(catalog);
 const filtered=filterMenu(catalog,'creme','food',true);
 assert.deepEqual(sortMenu(filtered,'price-low').map(x=>x.id),['d','e','a']);
 assert.deepEqual(sortMenu(filtered,'price-high').map(x=>x.id),['a','d','e']);
 assert.deepEqual(filtered.map(x=>x.id),['a','d','e']);
 assert.equal(JSON.stringify(catalog),original);
 assert.equal(sortMenu(filtered,'price-low')[0],catalog[3]);
});

test('catalog name sorting preserves stable API order for equal names and excludes unavailable items',()=>{
 const duplicates=[
  Object.freeze({id:'first',kind:'drink',name:'Café',available:true,priceCents:200}),
  Object.freeze({id:'excluded',kind:'drink',name:'Cafe',available:false,priceCents:100}),
  Object.freeze({id:'second',kind:'drink',name:'Cafe',available:true,priceCents:300})
 ];
 const result=sortMenu(filterMenu(duplicates,'cafe','drink',true),'name');
 assert.deepEqual(result.map(x=>x.id),['first','second']);
 assert.deepEqual(duplicates.map(x=>x.id),['first','excluded','second']);
});

test('invalid presentation sort fails closed rather than silently changing the selected ordering',()=>{
 assert.throws(()=>sortMenu(catalog,'price-random'),TypeError);
 assert.throws(()=>sortMenu(null,'default'),TypeError);
 assert.throws(()=>filterMenu(catalog,'creme','food','true'),TypeError);
});

import test from 'node:test';
import assert from 'node:assert/strict';
import {filterMenu,sortMenu} from '../src/menuViewModel.js';

const items=[
 {id:'b',kind:'food',name:'Zucchini',priceCents:800,available:true},
 {id:'a',kind:'food',name:'Apple',priceCents:500,available:true},
 {id:'c',kind:'drink',name:'Café',priceCents:500,available:false},
 {id:'d',kind:'drink',name:'Water',priceCents:200,available:true}
];

test('catalog ordering is immutable and default retains Python order',()=>{
 const before=JSON.stringify(items);
 const result=sortMenu(items);
 assert.deepEqual(result,items);
 assert.notStrictEqual(result,items);
 assert.equal(JSON.stringify(items),before);
});

test('catalog sorting supports name and both price directions with stable ties',()=>{
 assert.deepEqual(sortMenu(items,'name').map(x=>x.id),['a','c','d','b']);
 assert.deepEqual(sortMenu(items,'price-low').map(x=>x.id),['d','a','c','b']);
 assert.deepEqual(sortMenu(items,'price-high').map(x=>x.id),['b','a','c','d']);
});

test('sorting applies after read-only type, search and availability filters',()=>{
 const filtered=filterMenu(items,'','food',true);
 assert.deepEqual(sortMenu(filtered,'price-low').map(x=>x.id),['a','b']);
 assert.deepEqual(sortMenu(filterMenu(items,'','all',true),'name').map(x=>x.id),['a','d','b']);
});

test('invalid ordering fails closed without mutating API data',()=>{
 const before=JSON.stringify(items);
 assert.throws(()=>sortMenu(items,'unknown'),TypeError);
 assert.throws(()=>sortMenu(null),TypeError);
 assert.equal(JSON.stringify(items),before);
});

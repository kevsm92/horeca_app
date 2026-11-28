import test from 'node:test';
import assert from 'node:assert/strict';
import {filterMenu,sortMenu} from '../src/menuViewModel.js';

const items=Object.freeze([
 Object.freeze({id:'a',kind:'food',name:'Fish & Chips',description:'House-made tartar',available:true,priceCents:1350}),
 Object.freeze({id:'b',kind:'drink',name:'Café-crème',description:'Hot espresso drink',available:true,priceCents:450}),
 Object.freeze({id:'c',kind:'food',name:'Fish pie',description:'Chips on request',available:false,priceCents:1200})
]);

test('punctuation and accents normalize across name and description without modifying records',()=>{
 const before=JSON.stringify(items);
 assert.deepEqual(filterMenu(items,'fish chips').map(item=>item.id),['a','c']);
 assert.deepEqual(filterMenu(items,'CAFE creme','drink').map(item=>item.id),['b']);
 assert.deepEqual(filterMenu(items,'tartar house').map(item=>item.id),['a']);
 assert.equal(JSON.stringify(items),before);
});

test('symbol-only and whitespace-only searches do not hide venue catalog items',()=>{
 for(const query of ['  ', ' & — ! ', '\n\t']){
  assert.deepEqual(filterMenu(items,query).map(item=>item.id),['a','b','c']);
 }
 assert.deepEqual(filterMenu(items,' & — ! ','food',true).map(item=>item.id),['a']);
});

test('display ordering retains API item identity and original order after filtering',()=>{
 const selected=filterMenu(items,'fish');
 assert.deepEqual(sortMenu(selected,'price-low').map(item=>item.id),['c','a']);
 assert.deepEqual(selected.map(item=>item.id),['a','c']);
 assert.strictEqual(sortMenu(selected,'price-low')[0],items[2]);
 assert.notStrictEqual(sortMenu(selected,'default'),selected);
});

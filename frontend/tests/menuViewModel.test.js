import test from 'node:test';
import assert from 'node:assert/strict';
import {filterMenu} from '../src/menuViewModel.js';
const items=[{id:'soup',kind:'food',name:'Tomato Soup'},{id:'water',kind:'drink',name:'Sparkling Water'}];
test('filters authenticated catalog by food/drink and name',()=>{
 assert.deepEqual(filterMenu(items,' soup ','food'),[items[0]]);
 assert.deepEqual(filterMenu(items,'water','drink'),[items[1]]);
 assert.deepEqual(filterMenu(items,'','all'),items);
});
test('empty catalog and no matches stay empty',()=>{
 assert.deepEqual(filterMenu([]),[]);
 assert.deepEqual(filterMenu(items,'not here'),[]);
});
test('rejects malformed filter parameters',()=>{
 assert.throws(()=>filterMenu(null));
 assert.throws(()=>filterMenu(items,'','invalid'));
});

test('accent-insensitive search supports composed and decomposed Unicode without mutating catalog',()=>{
 const accented=[{id:'cafe',kind:'drink',name:'Café crème'},{id:'jalapeno',kind:'food',name:'Jalapeño tapas'},{id:'brulee',kind:'food',name:'Crème brûlée'}];
 const snapshot=JSON.stringify(accented);
 assert.deepEqual(filterMenu(accented,' CAFE ','drink'),[accented[0]]);
 assert.deepEqual(filterMenu(accented,'jalapeno','food'),[accented[1]]);
 assert.deepEqual(filterMenu(accented,'bru\u0302le\u0301e','food'),[accented[2]]);
 assert.deepEqual(filterMenu(accented,'cafe','food'),[]);
 assert.equal(JSON.stringify(accented),snapshot);
});

test('search tolerates repeated and nonbreaking whitespace in catalog and input',()=>{
 const catalog=[{id:'one',kind:'food',name:'Crème\u00a0\u00a0brûlée'},{id:'two',kind:'drink',name:'Iced\n Coffee'}];
 const snapshot=JSON.stringify(catalog);
 assert.deepEqual(filterMenu(catalog,'  creme   brulee  ','food'),[catalog[0]]);
 assert.deepEqual(filterMenu(catalog,'iced\tcoffee','drink'),[catalog[1]]);
 assert.deepEqual(filterMenu(catalog,'coffee','food'),[]);
 assert.equal(JSON.stringify(catalog),snapshot);
});

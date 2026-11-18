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

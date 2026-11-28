import test from 'node:test';
import assert from 'node:assert/strict';
import {filterMenu} from '../src/menuViewModel.js';

test('catalog search treats question marks, exclamation points and quotation marks as word boundaries',()=>{
  const catalog=[
    {id:'a',kind:'food',name:'“Chef’s choice!”',description:'Fresh? Yes!',available:true},
    {id:'b',kind:'drink',name:'«Iced» tea',description:'House favourite',available:false}
  ];
  const before=JSON.stringify(catalog);
  assert.deepEqual(filterMenu(catalog,'chef choice','food'),[catalog[0]]);
  assert.deepEqual(filterMenu(catalog,'fresh yes','food',true),[catalog[0]]);
  assert.deepEqual(filterMenu(catalog,'iced tea','drink'),[catalog[1]]);
  assert.deepEqual(filterMenu(catalog,'"iced" tea','drink',true),[]);
  assert.deepEqual(filterMenu(catalog,'chef? choice!','drink'),[]);
  assert.equal(JSON.stringify(catalog),before);
});

import test from 'node:test';
import assert from 'node:assert/strict';
import {catalogCartLines,changeCatalogQuantity} from '../src/catalogCart.js';
const items=[{id:'demo-food-1',name:'Fictional Soup',priceCents:650,available:true},{id:'demo-drink-1',name:'Fictional Water',priceCents:320,available:true},{id:'sold-out',name:'Unavailable',priceCents:200,available:false}];
test('uses stable Python catalog IDs and integer-cent line totals',()=>{
  assert.deepEqual(catalogCartLines(items,{'demo-food-1':2,'demo-drink-1':1}),{lines:[{id:'demo-food-1',name:'Fictional Soup',quantity:2,unitPriceCents:650,lineCents:1300},{id:'demo-drink-1',name:'Fictional Water',quantity:1,unitPriceCents:320,lineCents:320}],totalCents:1620});
});
test('rejects unavailable, stale or cross-catalog IDs',()=>{
  for(const id of ['sold-out','missing','__proto__'])assert.throws(()=>catalogCartLines(items,{[id]:1}),/Unknown or unavailable/);
});
test('rejects fractional, negative, zero, oversized or nonnumeric quantities',()=>{
  for(const q of [0,-1,1.5,100,'2',NaN])assert.throws(()=>catalogCartLines(items,{'demo-food-1':q}),/quantity/);
});
test('refuses invalid item prices, duplicate IDs and excessive totals',()=>{
  for(const bad of [{...items[0],priceCents:1.2},{...items[0],priceCents:-1}])assert.throws(()=>catalogCartLines([bad],{}),/item/);
  assert.throws(()=>catalogCartLines([items[0],items[0]],{}),/item/);
  const pricey=Array.from({length:2},(_,i)=>({id:'price-'+i,name:'Synthetic',priceCents:10000000,available:true}));
  assert.throws(()=>catalogCartLines(pricey,{'price-0':99,'price-1':99}),/total limit/);
});
test('increments and decrements without mutating existing cart',()=>{
  const original={'demo-food-1':1};
  const increased=changeCatalogQuantity(items,original,'demo-food-1',1);
  assert.deepEqual(original,{'demo-food-1':1});assert.deepEqual(increased,{'demo-food-1':2});
  assert.deepEqual(changeCatalogQuantity(items,{'demo-food-1':1},'demo-food-1',-1),{});
});
test('cannot add unavailable items, remove absent items or exceed quantity cap',()=>{
  assert.throws(()=>changeCatalogQuantity(items,{},'sold-out',1),/unavailable/);
  assert.throws(()=>changeCatalogQuantity(items,{},'demo-food-1',-1),/limit/);
  assert.throws(()=>changeCatalogQuantity(items,{'demo-food-1':99},'demo-food-1',1),/limit/);
});
test('empty catalog and empty cart produce a zero total',()=>assert.deepEqual(catalogCartLines([],{}),{lines:[],totalCents:0}));

test('prototype-like stable IDs remain ordinary cart keys without prototype mutation',()=>{
  const special=[{id:'__proto__',name:'Synthetic Special',priceCents:275,available:true},
                 {id:'constructor',name:'Synthetic Constructor',priceCents:125,available:true}];
  const first=changeCatalogQuantity(special,{},'__proto__',1);
  assert.equal(Object.getPrototypeOf(first),Object.prototype);
  assert.equal(Object.hasOwn(first,'__proto__'),true);
  assert.equal(first['__proto__'],1);
  const second=changeCatalogQuantity(special,first,'constructor',1);
  assert.equal(second.constructor,1);
  assert.equal(Object.getPrototypeOf(second),Object.prototype);
  assert.equal(catalogCartLines(special,second).totalCents,400);
  const third=changeCatalogQuantity(special,second,'__proto__',-1);
  assert.equal(Object.hasOwn(third,'__proto__'),false);
  assert.equal(catalogCartLines(special,third).totalCents,125);
});

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

test('catalog search includes optional descriptions without changing kind filtering',()=>{
 const catalog=[{id:'one',kind:'food',name:'Seasonal plate',description:'Roasted aubergine with herbs'},{id:'two',kind:'drink',name:'House special',description:'Café au lait'},{id:'three',kind:'food',name:'Soup',description:null}];
 const snapshot=JSON.stringify(catalog);
 assert.deepEqual(filterMenu(catalog,'aubergine','food'),[catalog[0]]);
 assert.deepEqual(filterMenu(catalog,'cafe','drink'),[catalog[1]]);
 assert.deepEqual(filterMenu(catalog,'cafe','food'),[]);
 assert.deepEqual(filterMenu(catalog,'soup','food'),[catalog[2]]);
 assert.equal(JSON.stringify(catalog),snapshot);
});

test('multi-term search spans product name and description regardless of term order',()=>{
 const catalog=[
  {id:'one',kind:'food',name:'Autumn Bowl',description:'Roasted pumpkin and sage'},
  {id:'two',kind:'drink',name:'Pumpkin Latte',description:'Warm spices'},
  {id:'three',kind:'food',name:'Autumn Salad',description:'Fresh herbs'}
 ];
 const snapshot=JSON.stringify(catalog);
 assert.deepEqual(filterMenu(catalog,'sage autumn','food'),[catalog[0]]);
 assert.deepEqual(filterMenu(catalog,'  PUMPKIN   bowl  ','all'),[catalog[0]]);
 assert.deepEqual(filterMenu(catalog,'pumpkin','drink'),[catalog[1]]);
 assert.deepEqual(filterMenu(catalog,'sage autumn','drink'),[]);
 assert.equal(JSON.stringify(catalog),snapshot);
});

test('rejects non-string catalog search queries without mutating products',()=>{
 const snapshot=JSON.stringify(items);
 for(const query of [null,42,{},['soup']]){
  assert.throws(()=>filterMenu(items,query,'all'),TypeError);
 }
 assert.equal(JSON.stringify(items),snapshot);
});

test('empty search and excluded product types avoid reading searchable fields',()=>{
 const food={id:'food',kind:'food',get name(){throw Error('name should not be read');},get description(){throw Error('description should not be read');}};
 const drink={id:'drink',kind:'drink',name:'Mint Tea',description:'Fresh mint'};
 assert.deepEqual(filterMenu([food,drink],'','all'),[food,drink]);
 assert.deepEqual(filterMenu([food,drink],'mint','drink'),[drink]);
});

test('multi-term catalog search reads each searchable field once per candidate',()=>{
 let names=0,descriptions=0;
 const food={kind:'food',get name(){names++;return 'Autumn Bowl';},get description(){descriptions++;return 'Roasted pumpkin and sage';}};
 assert.deepEqual(filterMenu([food],'pumpkin autumn sage','food'),[food]);
 assert.equal(names,1);
 assert.equal(descriptions,1);
});

test('hyphen and slash separated menu terms match space-separated input',()=>{
 const catalog=[{id:'one',kind:'food',name:'Gluten-free bread',description:'House-baked daily'},{id:'two',kind:'drink',name:'Orange/lemon spritz',description:null},{id:'three',kind:'food',name:'Gluten bread',description:null}];
 const snapshot=JSON.stringify(catalog);
 assert.deepEqual(filterMenu(catalog,'gluten free','food'),[catalog[0]]);
 assert.deepEqual(filterMenu(catalog,'house baked','food'),[catalog[0]]);
 assert.deepEqual(filterMenu(catalog,'orange lemon','drink'),[catalog[1]]);
 assert.deepEqual(filterMenu(catalog,'gluten-free','food'),[catalog[0]]);
 assert.deepEqual(filterMenu(catalog,'orange/lemon','food'),[]);
 assert.equal(JSON.stringify(catalog),snapshot);
});

test('typographic dash and slash search works across product descriptions',()=>{
 const catalog=[
  {id:'one',kind:'food',name:'Chef’s special',description:'Slow–roasted vegetables / crème fraîche'},
  {id:'two',kind:'drink',name:'Lime—mint cooler',description:'Alcohol-free'},
  {id:'three',kind:'food',name:'Vegetable soup',description:'Served hot'}
 ];
 const snapshot=JSON.stringify(catalog);
 assert.deepEqual(filterMenu(catalog,'slow roasted creme fraiche','food'),[catalog[0]]);
 assert.deepEqual(filterMenu(catalog,'lime mint','drink'),[catalog[1]]);
 assert.deepEqual(filterMenu(catalog,'alcohol free','drink'),[catalog[1]]);
 assert.deepEqual(filterMenu(catalog,'lime mint','food'),[]);
 assert.equal(JSON.stringify(catalog),snapshot);
});

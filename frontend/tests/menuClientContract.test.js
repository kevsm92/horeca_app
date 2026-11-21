import test from 'node:test';
import assert from 'node:assert/strict';
import {loadMenu,parseMenuResponse} from '../src/menuClient.js';

const sample={item_id:'synthetic-coffee',kind:'drink',name:'Test Coffee',price_cents:350,available:true,description:null};
const response=(status,payload={items:[sample]},contentType='application/json')=>({
  status,ok:status>=200&&status<300,
  headers:{get:key=>key.toLowerCase()==='content-type'?contentType:null},
  json:async()=>payload
});

test('normalizes authenticated venue menu items with integer-cent prices',()=>{
  assert.deepEqual(parseMenuResponse({items:[sample]}),[{id:'synthetic-coffee',kind:'drink',name:'Test Coffee',priceCents:350,available:true,description:null}]);
});
test('rejects duplicate, malformed, or unsafe product records',()=>{
  for(const payload of [
    {items:[sample,sample]},
    {items:[{...sample,item_id:'bad/id'}]},
    {items:[{...sample,price_cents:3.5}]},
    {items:[{...sample,available:'yes'}]},
    {items:[{...sample,name:'   '}]},
    {items:[{...sample,kind:'service'}]},
    {items:'not an array'}
  ])assert.throws(()=>parseMenuResponse(payload),TypeError);
});
test('uses same-origin authenticated endpoint without client-supplied venue',async()=>{
  const calls=[];
  const items=await loadMenu({fetchImpl:async(url,options)=>{calls.push({url,options});return response(200);}});
  assert.equal(items[0].priceCents,350);
  assert.equal(calls[0].url,'/api/v1/menu-items');
  assert.equal(calls[0].options.credentials,'same-origin');
  assert.equal(calls[0].options.redirect,'error');
  assert.equal(calls[0].options.method,'GET');
});
test('permits only fixed food and drink filters',async()=>{
  await assert.rejects(loadMenu({kind:'other',fetchImpl:async()=>response(200)}),TypeError);
  let requested='';
  await loadMenu({kind:'drink',fetchImpl:async url=>{requested=url;return response(200);}});
  assert.equal(requested,'/api/v1/menu-items?kind=drink');
});
test('never substitutes demonstration products on authentication failures',async()=>{
  for(const status of [401,403])await assert.rejects(loadMenu({fetchImpl:async()=>response(status)}),error=>error.code==='AUTH');
});
test('rejects server errors and non-JSON responses',async()=>{
  await assert.rejects(loadMenu({fetchImpl:async()=>response(500)}),error=>error.code==='UNAVAILABLE');
  await assert.rejects(loadMenu({fetchImpl:async()=>response(200,{items:[sample]},'text/html')}),TypeError);
});
test('forwards cancellation signal to fetch',async()=>{
  const controller=new AbortController();
  let observed;
  await loadMenu({signal:controller.signal,fetchImpl:async(_url,options)=>{observed=options.signal;return response(200);}});
  assert.equal(observed,controller.signal);
});

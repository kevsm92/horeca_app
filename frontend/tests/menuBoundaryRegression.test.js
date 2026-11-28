import test from 'node:test';
import assert from 'node:assert/strict';
import {loadMenu} from '../src/menuClient.js';

const response = (payload, {status=200,type='application/json'}={}) => ({
  status, ok:status>=200&&status<300,
  headers:{get:name=>name.toLowerCase()==='content-type'?type:null},
  json:async()=>payload
});
const valid={items:[{item_id:'drink_1',kind:'drink',name:'Water',price_cents:250,available:true,description:null}]};

test('menu reads use only the same-origin versioned Python route and never follow redirects',async()=>{
  let called=0;
  const items=await loadMenu({fetchImpl:async(url,options)=>{
    called++;
    assert.equal(url,'/api/v1/menu-items');
    assert.equal(options.method,'GET');
    assert.equal(options.credentials,'same-origin');
    assert.equal(options.cache,'no-store');
    assert.equal(options.redirect,'error');
    assert.equal(options.headers.Accept,'application/json');
    return response(valid);
  }});
  assert.equal(called,1);
  assert.equal(items[0].id,'drink_1');
});

test('menu authorization errors never publish synthetic fallback items',async()=>{
  for(const status of [401,403]){
    await assert.rejects(loadMenu({fetchImpl:async()=>response(valid,{status})}),error=>error.code==='AUTH');
  }
});

test('cancelled menu reads never start transport or publish late JSON',async()=>{
  const early=new AbortController();
  early.abort();
  let called=false;
  await assert.rejects(loadMenu({signal:early.signal,fetchImpl:async()=>{called=true;return response(valid);}}),{name:'AbortError'});
  assert.equal(called,false);

  const late=new AbortController();
  await assert.rejects(loadMenu({signal:late.signal,fetchImpl:async()=>({
    ...response(valid),
    json:async()=>{late.abort();return valid;}
  })}),{name:'AbortError'});
});

test('malformed or non-JSON menu responses fail closed',async()=>{
  const malformed=[{items:[{...valid.items[0],price_cents:-1}]},{items:[valid.items[0],valid.items[0]]},{items:'not an array'}];
  for(const payload of malformed){
    await assert.rejects(loadMenu({fetchImpl:async()=>response(payload)}),TypeError);
  }
  await assert.rejects(loadMenu({fetchImpl:async()=>response(valid,{type:'text/html'})}),TypeError);
});

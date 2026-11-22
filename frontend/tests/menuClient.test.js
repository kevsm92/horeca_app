import test from 'node:test';
import assert from 'node:assert/strict';
import {loadMenu,parseMenuResponse} from '../src/menuClient.js';
const item={item_id:'demo-food-1',kind:'food',name:'Fictional Soup',price_cents:650,available:true,description:'Synthetic'};
const response=(status=200,items=[item],type='application/json; charset=utf-8')=>({status,ok:status>=200&&status<300,headers:{get:()=>type},json:async()=>({items})});
test('maps Python SQLite menu contract to typed client records',()=>{assert.deepEqual(parseMenuResponse({items:[item]}),[{id:'demo-food-1',kind:'food',name:'Fictional Soup',priceCents:650,available:true,description:'Synthetic'}]);});
test('authenticated same-origin read has no venue override',async()=>{let args;const items=await loadMenu({fetchImpl:async(...a)=>{args=a;return response();},kind:'food'});assert.equal(args[0],'/api/v1/menu-items?kind=food');assert.equal(args[1].method,'GET');assert.equal(args[1].credentials,'same-origin');assert.equal(args[1].redirect,'error');assert.equal(items.length,1);});
test('fails closed on unauthorized or unavailable response',async()=>{for(const status of [401,403,404,503])await assert.rejects(loadMenu({fetchImpl:async()=>response(status)}),e=>e.code===(status<404?'AUTH':'UNAVAILABLE'));});
test('rejects malformed menu records and duplicates',()=>{for(const bad of [{...item,price_cents:1.5},{...item,available:1},{...item,item_id:'../bad'},{...item,kind:'other'},{...item,name:''},{...item,price_cents:-1}])assert.throws(()=>parseMenuResponse({items:[bad]}));assert.throws(()=>parseMenuResponse({items:[item,item]}));});
test('rejects HTML, invalid filters and missing items',async()=>{await assert.rejects(loadMenu({fetchImpl:async()=>response(200,[item],'text/html')}),/not JSON/);await assert.rejects(loadMenu({kind:'venue=other',fetchImpl:async()=>response()}),/filter/);assert.throws(()=>parseMenuResponse({}));});
test('supports empty catalog and abort propagation',async()=>{assert.deepEqual(await loadMenu({fetchImpl:async()=>response(200,[])}),[]);const c=new AbortController();c.abort();await assert.rejects(loadMenu({signal:c.signal,fetchImpl:async(_url,{signal})=>{if(signal.aborted)throw new Error('aborted');}}),/aborted/);});

test('network errors and malformed JSON fail closed without synthetic fallback',async()=>{
  await assert.rejects(loadMenu({fetchImpl:async()=>{throw new TypeError('Network unavailable');}}),/Network unavailable/);
  await assert.rejects(loadMenu({fetchImpl:async()=>({...response(),json:async()=>{throw new SyntaxError('Invalid JSON');}})}),/Invalid JSON/);
  await assert.rejects(loadMenu({fetchImpl:async()=>({...response(),json:async()=>({items:'not an array'})})}),/Invalid menu response/);
});
test('catalog contract enforces bounded records and nonnegative integer-cent prices',()=>{
  assert.throws(()=>parseMenuResponse({items:Array.from({length:5001},()=>item)}),/Invalid menu response/);
  for(const bad of [{...item,price_cents:10000001},{...item,price_cents:NaN},{...item,name:'x'.repeat(201)},{...item,description:'x'.repeat(2001)}])
    assert.throws(()=>parseMenuResponse({items:[bad]}),/Invalid menu item/);
  assert.deepEqual(parseMenuResponse({items:[{...item,description:null}]} )[0].description,null);
});
test('menu read uses only an explicit JSON Accept header and forwards abort signal',async()=>{
  const controller=new AbortController();
  let options;
  await loadMenu({signal:controller.signal,fetchImpl:async(_url,request)=>{options=request;return response();}});
  assert.deepEqual(options.headers,{Accept:'application/json'});
  assert.equal(options.signal,controller.signal);
  assert.equal(options.body,undefined);
});

test('late menu JSON response is rejected after cancellation, not exposed as venue data',async()=>{
  const controller=new AbortController();
  let resolveBody;
  const fetchImpl=async()=>({...response(),json:()=>new Promise(resolve=>{resolveBody=resolve;})});
  const pending=loadMenu({fetchImpl,signal:controller.signal});
  await Promise.resolve();
  assert.equal(typeof resolveBody,'function');
  controller.abort();
  resolveBody({items:[item]});
  await assert.rejects(pending,error=>error?.name==='AbortError');
});

test('menu JSON response succeeds when the request is not cancelled',async()=>{
  const controller=new AbortController();
  assert.deepEqual(await loadMenu({fetchImpl:async()=>response(),signal:controller.signal}),
    parseMenuResponse({items:[item]}));
});

test('pre-aborted menu read never sends a request',async()=>{
  const controller=new AbortController();controller.abort();let calls=0;
  await assert.rejects(loadMenu({signal:controller.signal,fetchImpl:async()=>{calls++;return response();}}),error=>error?.name==='AbortError');
  assert.equal(calls,0);
});
test('menu read cancelled after fetch does not parse response body',async()=>{
  const controller=new AbortController();let reads=0;
  const fetchImpl=async()=>{controller.abort();return {...response(),json:async()=>{reads++;return {items:[item]};}};};
  await assert.rejects(loadMenu({signal:controller.signal,fetchImpl}),error=>error?.name==='AbortError');
  assert.equal(reads,0);
});

test('authenticated menu reads bypass browser caches to avoid stale venue catalogs',async()=>{
  let request;
  await loadMenu({fetchImpl:async(_url,options)=>{request=options;return response();}});
  assert.equal(request.cache,'no-store');
  assert.equal(request.credentials,'same-origin');
  assert.equal(request.redirect,'error');
});

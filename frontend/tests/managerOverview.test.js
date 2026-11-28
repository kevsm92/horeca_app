import test from 'node:test';
import assert from 'node:assert/strict';
import {demoDashboardMetrics,displayMetric,safeDemoDashboardMetrics} from '../src/dashboardMetrics.js';
const sample={tables:[{guests:2},{guests:0}],orders:[{status:'New'},{status:'Ready'}],orderValueCents:1250};
test('fictional operational counts reflect browser state, not a live API',()=>{const metrics=demoDashboardMetrics(sample);assert.equal(metrics.find(m=>m.id==='occupied').value,'1 / 2');assert.equal(metrics.find(m=>m.id==='guests').value,'2');assert.equal(metrics.find(m=>m.id==='tickets').value,'1');assert.equal(metrics.find(m=>m.id==='orders').source,'demo');});
test('unknown workforce and payment data are unavailable rather than zero',()=>{const metrics=demoDashboardMetrics(sample);for(const id of ['presence','upcoming','revenue','requests']){const metric=displayMetric(metrics.find(m=>m.id===id));assert.equal(metric.value,'Unavailable');assert.equal(metric.status,'Not connected');}});
test('demo order value never claims captured revenue',()=>{const metrics=demoDashboardMetrics(sample);assert.match(metrics.find(m=>m.id==='orders').detail,/not captured revenue/);assert.equal(metrics.find(m=>m.id==='revenue').value,null);});
test('presentation rejects unknown source and absent demo values',()=>{assert.throws(()=>displayMetric({source:'live',value:4}),TypeError);assert.throws(()=>displayMetric({source:'demo',value:null}),TypeError);});

test('malformed synthetic KPI inputs fail closed instead of showing misleading counts',()=>{
  for (const bad of [
    {...sample,tables:null},
    {...sample,tables:[{guests:-1}]},
    {...sample,tables:[{guests:NaN}]},
    {...sample,orders:[null]},
    {...sample,orders:[{status:''}]},
    {...sample,orderValueCents:NaN},
    {...sample,orderValueCents:-1},
    {...sample,orderValueCents:1.5},
  ]) assert.throws(()=>demoDashboardMetrics(bad),TypeError);
});

test('fictional guest totals reject safe-integer overflow',()=>{
  assert.throws(()=>demoDashboardMetrics({...sample,tables:[{guests:Number.MAX_SAFE_INTEGER},{guests:1}]}),TypeError);
  assert.equal(demoDashboardMetrics({...sample,tables:[{guests:Number.MAX_SAFE_INTEGER}]}).find(m=>m.id==='guests').value,String(Number.MAX_SAFE_INTEGER));
});

test('manager KPI presentation degrades safely for corrupt synthetic fixtures',()=>{
  const valid=safeDemoDashboardMetrics(sample);
  assert.equal(valid.invalidDemoData,false);
  assert.equal(valid.metrics.find(m=>m.id==='occupied').value,'1 / 2');
  assert.equal(valid.metrics.find(m=>m.id==='revenue').value,'Unavailable');
  for (const input of [
    {...sample,tables:[{guests:-2}]},
    {...sample,orders:[{status:''}]},
    {...sample,orderValueCents:Number.POSITIVE_INFINITY},
    {...sample,tables:[{guests:Number.MAX_SAFE_INTEGER},{guests:1}]},
  ]) {
    const result=safeDemoDashboardMetrics(input);
    assert.equal(result.invalidDemoData,true);
    assert.deepEqual(result.metrics,[]);
  }
});

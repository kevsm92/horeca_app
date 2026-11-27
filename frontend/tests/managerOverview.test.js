import test from 'node:test';
import assert from 'node:assert/strict';
import {demoDashboardMetrics,displayMetric} from '../src/dashboardMetrics.js';
const sample={tables:[{guests:2},{guests:0}],orders:[{status:'New'},{status:'Ready'}],orderValueCents:1250};
test('fictional operational counts reflect browser state, not a live API',()=>{const metrics=demoDashboardMetrics(sample);assert.equal(metrics.find(m=>m.id==='occupied').value,'1 / 2');assert.equal(metrics.find(m=>m.id==='guests').value,'2');assert.equal(metrics.find(m=>m.id==='tickets').value,'1');assert.equal(metrics.find(m=>m.id==='orders').source,'demo');});
test('unknown workforce and payment data are unavailable rather than zero',()=>{const metrics=demoDashboardMetrics(sample);for(const id of ['presence','upcoming','revenue','requests']){const metric=displayMetric(metrics.find(m=>m.id===id));assert.equal(metric.value,'Unavailable');assert.equal(metric.status,'Not connected');}});
test('demo order value never claims captured revenue',()=>{const metrics=demoDashboardMetrics(sample);assert.match(metrics.find(m=>m.id==='orders').detail,/not captured revenue/);assert.equal(metrics.find(m=>m.id==='revenue').value,null);});
test('presentation rejects unknown source and absent demo values',()=>{assert.throws(()=>displayMetric({source:'live',value:4}),TypeError);assert.throws(()=>displayMetric({source:'demo',value:null}),TypeError);});

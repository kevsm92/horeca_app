import test from 'node:test';
import assert from 'node:assert/strict';
import {parseManagerHistory,HistoryContractError,HISTORY_METRICS} from '../src/managerHistoryContract.js';
const valid = () => ({schema_version:1,venue_id:'venue-a',range:'week',generated_at:'2026-11-27T02:00:00Z',timezone:'Europe/Brussels',currency:'EUR',period_start:'2026-11-23',period_end:'2026-11-29',series:HISTORY_METRICS.map(metric=>({metric,unit:metric==='captured_revenue'?'minor_currency':'count',points:[{at:'2026-11-23T12:00:00Z',value:0}]}))});
const parse = p => parseManagerHistory(p,{expectedVenueId:'venue-a',range:'week'});
test('accepts validated versioned venue-scoped historical series without manufacturing data',()=>{const result=parse(valid());assert.equal(result.series.length,4);assert.equal(result.series[1].points[0].value,0);assert.ok(Object.isFrozen(result.series[0].points));});
test('rejects cross-venue, wrong-range, unknown version and missing trusted context',()=>{for(const patch of [{venue_id:'venue-b'},{range:'day'},{schema_version:2}]) assert.throws(()=>parse({...valid(),...patch}),HistoryContractError);assert.throws(()=>parseManagerHistory(valid(),{range:'week'}),HistoryContractError);});
test('rejects malformed, duplicate or missing series',()=>{for(const series of [[],[...valid().series.slice(0,3),valid().series[0]],valid().series.map((s,i)=>i===0?{...s,metric:'revenue'}:s)])assert.throws(()=>parse({...valid(),series}),HistoryContractError);});
test('rejects negative, fractional, unsafe and unordered point values',()=>{for(const value of [-1,0.5,Number.MAX_SAFE_INTEGER+1,NaN]){const p=valid();p.series[0].points[0].value=value;assert.throws(()=>parse(p),HistoryContractError);}const p=valid();p.series[0].points.push({at:'2026-11-22T12:00:00Z',value:1});assert.throws(()=>parse(p),HistoryContractError);});
test('rejects invalid periods, timestamps, units and currency',()=>{for(const patch of [{period_start:'2026-02-30'},{period_end:'2026-11-01'},{generated_at:'yesterday'},{currency:'€'}])assert.throws(()=>parse({...valid(),...patch}),HistoryContractError);const p=valid();p.series[1].unit='count';assert.throws(()=>parse(p),HistoryContractError);});

test('compares chronological instants rather than lexicographic offset strings',()=>{
  const validOffsets=valid();
  validOffsets.series[0].points=[
    {at:'2026-11-23T10:00:00+01:00',value:1},
    {at:'2026-11-23T09:30:00Z',value:2}
  ];
  assert.equal(parse(validOffsets).series[0].points.length,2);
  const reversed=valid();
  reversed.series[0].points=[
    {at:'2026-11-23T09:30:00Z',value:1},
    {at:'2026-11-23T10:00:00+01:00',value:2}
  ];
  assert.throws(()=>parse(reversed),HistoryContractError);
  const duplicate=valid();
  duplicate.series[0].points=[
    {at:'2026-11-23T09:00:00Z',value:1},
    {at:'2026-11-23T10:00:00+01:00',value:2}
  ];
  assert.throws(()=>parse(duplicate),HistoryContractError);
});

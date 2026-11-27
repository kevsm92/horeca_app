import test from 'node:test';
import assert from 'node:assert/strict';
import {HISTORICAL_RANGES,historicalRangeLabel,historicalEmptyMessage} from '../src/historicalMetrics.js';
test('all supported ranges are distinct and immutable',()=>{
 assert.deepEqual(HISTORICAL_RANGES.map(x=>x.id),['day','week','month']);
 assert.ok(Object.isFrozen(HISTORICAL_RANGES));
 assert.ok(HISTORICAL_RANGES.every(Object.isFrozen));
});
test('unavailable reporting is never represented as zero or live',()=>{
 for(const range of HISTORICAL_RANGES){
  const message=historicalEmptyMessage(range.id);
  assert.match(message,/No verified/);
  assert.match(message,/not a zero value or a live chart/);
  assert.ok(message.includes(range.label.toLowerCase()));
 }
});
test('invalid range cannot invent a reporting period',()=>{
 assert.equal(historicalRangeLabel('quarter'),'Week');
 assert.equal(historicalEmptyMessage('invalid'),historicalEmptyMessage('week'));
});

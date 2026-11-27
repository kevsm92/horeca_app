import test from 'node:test';
import assert from 'node:assert/strict';
import {FICTIONAL_WEEKLY_ORDERS,fictionalOrderBarPercent} from '../src/fictionalOrderPattern.js';

test('fictional order chart has exactly seven ordered weekdays and immutable data',()=>{
  assert.deepEqual(FICTIONAL_WEEKLY_ORDERS.map(item=>item.day),['Mon','Tue','Wed','Thu','Fri','Sat','Sun']);
  assert.ok(Object.isFrozen(FICTIONAL_WEEKLY_ORDERS));
  assert.ok(FICTIONAL_WEEKLY_ORDERS.every(Object.isFrozen));
  assert.ok(FICTIONAL_WEEKLY_ORDERS.every(item=>Number.isInteger(item.count)&&item.count>=0));
});
test('illustrative bar heights are bounded and reject malformed values',()=>{
  assert.equal(fictionalOrderBarPercent(28),100);
  assert.equal(fictionalOrderBarPercent(0),0);
  assert.equal(fictionalOrderBarPercent(-1),0);
  assert.equal(fictionalOrderBarPercent(NaN),0);
  assert.equal(fictionalOrderBarPercent(Infinity),0);
  assert.equal(fictionalOrderBarPercent(999),100);
  assert.ok(fictionalOrderBarPercent(8)>0);
});

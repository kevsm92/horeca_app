import test from 'node:test';
import assert from 'node:assert/strict';
import {HISTORICAL_VIEW_STATES,historicalViewMessage,historicalViewAccessibility} from '../src/historicalViewState.js';

test('every historical data state has a distinct, non-live message',()=>{
  assert.equal(new Set(HISTORICAL_VIEW_STATES.map(s=>historicalViewMessage(s).title)).size,HISTORICAL_VIEW_STATES.length);
  for(const state of HISTORICAL_VIEW_STATES){
    const result=historicalViewMessage(state);
    assert.equal(result.state,state);
    assert.ok(result.detail.length>10);
    assert.ok(Object.isFrozen(result));
    assert.doesNotMatch(result.title,/live/i);
  }
});
test('unauthorized access is never presented as empty data',()=>{
  assert.match(historicalViewMessage('forbidden').detail,/not authorized/);
  assert.notEqual(historicalViewMessage('forbidden').title,historicalViewMessage('empty').title);
});
test('stale and failed data cannot silently appear current',()=>{
  assert.match(historicalViewMessage('stale').detail,/not treat cached values as current/);
  assert.match(historicalViewMessage('error').detail,/No historical totals/);
});
test('unknown states fail closed',()=>{
  assert.throws(()=>historicalViewMessage('ready'),TypeError);
  assert.throws(()=>historicalViewMessage('__proto__'),TypeError);
  assert.equal(historicalViewMessage().state,'unavailable');
});

test('accessible announcements distinguish loading, errors, and denied access',()=>{
  for (const state of HISTORICAL_VIEW_STATES) {
    const props=historicalViewAccessibility(state);
    assert.ok(Object.isFrozen(props));
    assert.equal(props.busy,state==='loading');
    assert.equal(props.role,['error','forbidden'].includes(state)?'alert':'status');
    assert.equal(props.live,['error','forbidden'].includes(state)?'assertive':'polite');
  }
  assert.throws(()=>historicalViewAccessibility('ready'),TypeError);
});

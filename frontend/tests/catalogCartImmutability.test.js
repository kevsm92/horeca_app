import test from 'node:test';
import assert from 'node:assert/strict';
import {changeCatalogQuantity, removeCatalogLine, catalogCartLines} from '../src/catalogCart.js';

const items = Object.freeze([
  Object.freeze({id:'demo-a', name:'Synthetic A', priceCents:450, available:true}),
  Object.freeze({id:'demo-b', name:'Synthetic B', priceCents:200, available:true}),
  Object.freeze({id:'unavailable', name:'Synthetic unavailable', priceCents:100, available:false})
]);

test('frozen valid drafts can be edited without mutating the input', () => {
  const original = Object.freeze({'demo-a':2, 'demo-b':1});
  const adjusted = changeCatalogQuantity(items, original, 'demo-a', -1);
  assert.deepEqual(adjusted, {'demo-a':1, 'demo-b':1});
  assert.deepEqual(original, {'demo-a':2, 'demo-b':1});
  const removed = removeCatalogLine(items, original, 'demo-a');
  assert.deepEqual(removed, {'demo-b':1});
  assert.equal(catalogCartLines(items, removed).totalCents, 200);
  assert.deepEqual(original, {'demo-a':2, 'demo-b':1});
});

test('line removal rejects stale unrelated entries rather than silently repairing a draft', () => {
  for (const invalid of [
    {'demo-a':1, 'missing':1},
    {'demo-a':1, 'unavailable':1},
    {'demo-a':1, 'demo-b':0},
    {'demo-a':1, 'demo-b':'2'}
  ]) {
    const snapshot = {...invalid};
    assert.throws(() => removeCatalogLine(items, invalid, 'demo-a'));
    assert.deepEqual(invalid, snapshot);
  }
});

test('invalid adjustments never mutate an existing draft', () => {
  const draft = {'demo-a':1};
  for (const [id, delta] of [['missing',1], ['demo-a',2], ['demo-a',0], ['demo-a',0.5], ['demo-a',NaN]]) {
    assert.throws(() => changeCatalogQuantity(items, draft, id, delta));
    assert.deepEqual(draft, {'demo-a':1});
  }
});

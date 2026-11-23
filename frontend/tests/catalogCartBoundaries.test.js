import test from 'node:test';
import assert from 'node:assert/strict';
import { catalogCartLines, changeCatalogQuantity } from '../src/catalogCart.js';

const item = Object.freeze({ id: 'synthetic-item', name: 'Synthetic item', priceCents: 10000000, available: true });

test('99 units at the per-item cap remain a valid local projection', () => {
  const draft = Object.freeze({ 'synthetic-item': 99 });
  assert.equal(catalogCartLines([item], draft).totalCents, 990000000);
  assert.throws(() => changeCatalogQuantity([item], draft, 'synthetic-item', 1), /limit/);
  assert.equal(draft['synthetic-item'], 99);
});

test('exact aggregate total limit is accepted but the next cent is rejected', () => {
  const items = [
    item,
    { id: 'synthetic-extra', name: 'Synthetic extra', priceCents: 1000000, available: true }
  ];
  assert.equal(catalogCartLines(items, { 'synthetic-item': 99, 'synthetic-extra': 10 }).totalCents, 1000000000);
  assert.throws(() => catalogCartLines(items, { 'synthetic-item': 99, 'synthetic-extra': 11 }), /total limit/);
});

test('client projections reject unsafe and non-integer prices rather than rounding', () => {
  for (const priceCents of [NaN, Infinity, -1, 1.1, Number.MAX_SAFE_INTEGER]) {
    assert.throws(() => catalogCartLines([{ ...item, priceCents }], {}), /Invalid catalog item/);
  }
});

test('invalid aggregate adjustment preserves the original local draft', () => {
  const items = [item, { id: 'synthetic-extra', name: 'Synthetic extra', priceCents: 1000000, available: true }];
  const original = Object.freeze({ 'synthetic-item': 99, 'synthetic-extra': 10 });
  assert.throws(() => changeCatalogQuantity(items, original, 'synthetic-extra', 1), /total limit/);
  assert.deepEqual(original, { 'synthetic-item': 99, 'synthetic-extra': 10 });
});

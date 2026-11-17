import test from 'node:test';
import assert from 'node:assert/strict';
import { validateGuestCount, updateGuestCount, canSubmitOrder } from '../src/tableRules.js';

const tables = [{ id: 'T1', seats: 2, guests: 1 }, { id: 'T2', seats: 4, guests: 0 }];
test('seating increments without mutating source state', () => {
  const result = updateGuestCount(tables, 'T1', 1);
  assert.equal(result.ok, true);
  assert.equal(result.tables[0].guests, 2);
  assert.equal(tables[0].guests, 1);
  assert.equal(result.tables[1], tables[1]);
});
test('rejects overcapacity seating', () => {
  const result = updateGuestCount(tables, 'T1', 2);
  assert.equal(result.ok, false);
  assert.equal(result.tables, tables);
});
test('rejects negative occupancy', () => assert.equal(updateGuestCount(tables, 'T2', -1).ok, false));
test('rejects fractional occupancy changes', () => assert.equal(updateGuestCount(tables, 'T1', 0.5).ok, false));
test('rejects missing physical table', () => assert.equal(updateGuestCount(tables, 'T99', 1).ok, false));
test('rejects invalid physical capacity', () => assert.equal(validateGuestCount({ seats: 0 }, 0).ok, false));
test('requires positive integer-cent order total', () => {
  assert.equal(canSubmitOrder(tables[0], 0).ok, false);
  assert.equal(canSubmitOrder(tables[0], 10.5).ok, false);
});
test('requires seated guests before submitting', () => assert.equal(canSubmitOrder(tables[1], 100).ok, false));
test('allows an order at a valid seated table', () => assert.equal(canSubmitOrder(tables[0], 100).ok, true));
test('rejects inconsistent overcapacity table', () => assert.equal(canSubmitOrder({ seats: 2, guests: 3 }, 100).ok, false));

import test from 'node:test';
import assert from 'node:assert/strict';
import { parsePythonTables, PythonApiError } from '../src/pythonApi.js';

// Proposed /api/v1/tables contract; no authenticated Python endpoint is assumed.
test('read-only table response accepts empty and physical capacity boundary snapshots', () => {
  assert.deepEqual(parsePythonTables({ tables: [] }), []);
  const payload = Object.freeze({ tables: Object.freeze([
    Object.freeze({ id: 'T-min', seats: 1, guests: 0 }),
    Object.freeze({ id: 'T-full', seats: 100, guests: 100 })
  ]) });
  const rows = parsePythonTables(payload);
  assert.deepEqual(rows, payload.tables);
  assert.notStrictEqual(rows[0], payload.tables[0]);
  assert.ok(rows.every(Object.isFrozen));
  assert.equal(payload.tables[1].guests, 100);
});

test('read-only table response rejects nonfinite, fractional, and nonnumeric counts', () => {
  for (const value of [NaN, Infinity, -Infinity, 2.5, '2', null, true]) {
    for (const field of ['seats', 'guests']) {
      const row = { id: 'T1', seats: 4, guests: 2, [field]: value };
      assert.throws(() => parsePythonTables({ tables: [row] }),
        error => error instanceof PythonApiError && error.code === 'INVALID_RESPONSE',
        `${field}=${String(value)}`);
    }
  }
});

import test from 'node:test';
import assert from 'node:assert/strict';
import { parsePythonTables, PythonApiError } from '../src/pythonApi.js';

// Synthetic contract fixtures only; the proposed Python tables endpoint is not live-verified.
test('table capacity and occupancy reject numeric coercion and non-finite values', () => {
  for (const [seats, guests] of [
    ['4', 2], [4, '2'], [true, 0], [4, false], [null, 0],
    [4, null], [4.5, 2], [4, 1.5], [NaN, 0], [4, NaN],
    [Infinity, 0], [4, Infinity], [-Infinity, 0], [4, -Infinity]
  ]) {
    assert.throws(() => parsePythonTables({ tables: [{ id: 'T1', seats, guests }] }),
      error => error instanceof PythonApiError && error.code === 'INVALID_RESPONSE');
  }
});

test('table contract accepts physical occupancy endpoints without changing source objects', () => {
  const source = { tables: [{ id: 'T0', seats: 1, guests: 0 }, { id: 'T1', seats: 100, guests: 100 }] };
  const before = JSON.stringify(source);
  const parsed = parsePythonTables(source);
  assert.deepEqual(parsed, source.tables);
  assert.notStrictEqual(parsed[0], source.tables[0]);
  assert.ok(parsed.every(Object.isFrozen));
  assert.equal(JSON.stringify(source), before);
});

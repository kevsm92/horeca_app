import test from 'node:test';
import assert from 'node:assert/strict';
import { parsePythonTables, PythonApiError } from '../src/pythonApi.js';

const invalid = error => error instanceof PythonApiError && error.code === 'INVALID_RESPONSE';

test('rejects an invalid later row rather than exposing a partially valid venue snapshot', () => {
  const payload = { tables: [
    { id: 'T1', seats: 4, guests: 2 },
    { id: 'T2', seats: 2, guests: 3 }
  ] };
  assert.throws(() => parsePythonTables(payload), invalid);
  assert.deepEqual(payload.tables[0], { id: 'T1', seats: 4, guests: 2 });
});

test('rejects non-finite, unsafe and nonnumeric capacity/occupancy values', () => {
  for (const [seats, guests] of [
    [NaN, 0], [Infinity, 0], [4, -Infinity], [4, NaN],
    [Number.MAX_SAFE_INTEGER + 1, 0], [4, '2'], ['4', 2], [4, null]
  ]) {
    assert.throws(() => parsePythonTables({ tables: [{ id: 'T1', seats, guests }] }), invalid);
  }
});

test('normalization copies server rows without leaking fields or retaining mutable input references', () => {
  const source = { tables: [{ id: 'T1', seats: 4, guests: 2, privateNote: 'do not display' }] };
  const result = parsePythonTables(source);
  assert.deepEqual(result, [{ id: 'T1', seats: 4, guests: 2 }]);
  assert.notStrictEqual(result[0], source.tables[0]);
  source.tables[0].guests = 1;
  source.tables[0].privateNote = 'changed';
  assert.deepEqual(result, [{ id: 'T1', seats: 4, guests: 2 }]);
  assert.equal(Object.isFrozen(result[0]), true);
});

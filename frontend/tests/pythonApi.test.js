import test from 'node:test';
import assert from 'node:assert/strict';
import { createPythonTablesApi, parsePythonTables, PythonApiError } from '../src/pythonApi.js';

const valid = { tables: [{ id: 'T1', seats: 4, guests: 2 }] };
const reply = (payload = valid, contentType = 'application/json; charset=utf-8') => ({
  ok: true, status: 200, headers: { get: () => contentType }, json: async () => payload
});

test('client construction is offline and exposes read-only tables only', () => {
  let calls = 0;
  const api = createPythonTablesApi(() => { calls++; return reply(); });
  assert.equal(calls, 0);
  assert.deepEqual(Object.keys(api), ['listTables']);
  assert.equal(Object.isFrozen(api), true);
});
test('tables GET targets same-origin Python API without Node backend or credentials in URL', async () => {
  let request;
  const api = createPythonTablesApi(async (url, options) => { request = { url, options }; return reply(); });
  const rows = await api.listTables();
  assert.deepEqual(rows, valid.tables);
  assert.equal(request.url, '/api/v1/tables');
  assert.equal(request.options.method, 'GET');
  assert.equal(request.options.credentials, 'same-origin');
  assert.equal(request.options.headers.Accept, 'application/json');
  assert.equal(request.options.body, undefined);
});
test('response validation rejects bad capacity, occupancy and duplicate table IDs', () => {
  for (const tables of [
    [{ id: 'T1', seats: 0, guests: 0 }],
    [{ id: 'T1', seats: 101, guests: 0 }],
    [{ id: 'T1', seats: 3, guests: 4 }],
    [{ id: 'T1', seats: 3, guests: -1 }],
    [{ id: 'T1', seats: 3, guests: 1.5 }],
    [{ id: 'T1', seats: 3, guests: 1 }, { id: 'T1', seats: 3, guests: 0 }],
    [{ id: '', seats: 3, guests: 1 }]
  ]) assert.throws(() => parsePythonTables({ tables }), e => e.code === 'INVALID_RESPONSE');
});
test('rejects non-object and missing tables responses', () => {
  for (const payload of [null, [], {}, { tables: null }, { tables: {} }]) {
    assert.throws(() => parsePythonTables(payload), e => e.code === 'INVALID_RESPONSE');
  }
});
test('rejects HTML response instead of interpreting an app shell as data', async () => {
  const api = createPythonTablesApi(async () => reply(valid, 'text/html'));
  await assert.rejects(api.listTables(), e => e.code === 'INVALID_RESPONSE');
});
test('rejects API errors with HTTP status preserved', async () => {
  const api = createPythonTablesApi(async () => ({ ok: false, status: 403 }));
  await assert.rejects(api.listTables(), e => e instanceof PythonApiError && e.code === 'HTTP_ERROR' && e.status === 403);
});
test('rejects malformed JSON', async () => {
  const api = createPythonTablesApi(async () => ({ ...reply(), json: async () => { throw Error('bad JSON'); } }));
  await assert.rejects(api.listTables(), e => e.code === 'INVALID_RESPONSE');
});
test('network failure stays explicit and does not fabricate fallback venue data', async () => {
  const api = createPythonTablesApi(async () => { throw Error('offline'); });
  await assert.rejects(api.listTables(), e => e.code === 'NETWORK_ERROR');
});
test('parser strips unexpected fields and freezes normalized rows', () => {
  const rows = parsePythonTables({ tables: [{ id: 'T1', seats: 4, guests: 2, adminToken: 'untrusted' }] });
  assert.deepEqual(rows, valid.tables);
  assert.equal(Object.isFrozen(rows[0]), true);
});

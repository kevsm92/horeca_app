import test from 'node:test';
import assert from 'node:assert/strict';
import { createPythonTablesApi } from '../src/pythonApi.js';

// Synthetic transport only: the Python tables endpoint remains unverified.
test('pre-aborted table view never initiates a Python API request', async () => {
  const controller = new AbortController();
  controller.abort();
  let calls = 0;
  const api = createPythonTablesApi(async () => {
    calls++;
    throw new Error('Cancelled view must not issue a request');
  });
  await assert.rejects(api.listTables({ signal: controller.signal }), { name: 'AbortError' });
  assert.equal(calls, 0);
});

test('non-aborted table view still reads through the injected Python API transport', async () => {
  let calls = 0;
  const api = createPythonTablesApi(async () => {
    calls++;
    return {
      ok: true,
      headers: { get: () => 'application/json' },
      json: async () => ({ tables: [{ id: 'synthetic-T1', seats: 4, guests: 0 }] })
    };
  });
  assert.deepEqual(await api.listTables(), [{ id: 'synthetic-T1', seats: 4, guests: 0 }]);
  assert.equal(calls, 1);
});

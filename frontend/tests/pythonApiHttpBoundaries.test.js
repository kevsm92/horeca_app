import test from 'node:test';
import assert from 'node:assert/strict';
import { createPythonTablesApi, PythonApiError } from '../src/pythonApi.js';

// Synthetic HTTP responses only; the proposed Python tables endpoint is not live-verified.
test('authentication, authorization and concurrency HTTP failures never return synthetic tables', async () => {
  for (const status of [401, 403, 409, 429, 500, 503]) {
    const api = createPythonTablesApi(async () => ({
      ok: false, status, headers: { get: () => 'application/json' },
      json: async () => ({ tables: [{ id: 'T1', seats: 4, guests: 2 }] })
    }));
    await assert.rejects(api.listTables(), error =>
      error instanceof PythonApiError && error.code === 'HTTP_ERROR' && error.status === status
    );
  }
});

test('an authorized empty table collection remains empty without demo fallback', async () => {
  const api = createPythonTablesApi(async () => ({
    ok: true, status: 200, headers: { get: () => 'application/json' },
    json: async () => ({ tables: [] })
  }));
  assert.deepEqual(await api.listTables(), []);
});

import test from 'node:test';
import assert from 'node:assert/strict';
import { createPythonTablesApi } from '../src/pythonApi.js';

const valid = { tables: [{ id: 'T1', seats: 4, guests: 2 }] };

test('abort after successful JSON read prevents stale table data from being returned', async () => {
  const controller = new AbortController();
  const api = createPythonTablesApi(async () => ({
    ok: true,
    headers: { get: () => 'application/json' },
    async json() { controller.abort(); return valid; }
  }));
  await assert.rejects(api.listTables({ signal: controller.signal }), error => error.name === 'AbortError');
});

test('successful JSON response remains usable when no cancellation occurs', async () => {
  const controller = new AbortController();
  const api = createPythonTablesApi(async () => ({
    ok: true,
    headers: { get: () => 'application/json' },
    async json() { return valid; }
  }));
  assert.deepEqual(await api.listTables({ signal: controller.signal }), valid.tables);
});

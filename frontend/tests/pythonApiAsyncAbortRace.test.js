import test from 'node:test';
import assert from 'node:assert/strict';
import { createPythonTablesApi } from '../src/pythonApi.js';

// Synthetic response only: the Python tables endpoint is not verified.
test('asynchronous cancellation after headers rejects a late successful body', async () => {
  const controller = new AbortController();
  let resolveBody;
  let bodyStarted;
  const started = new Promise(resolve => { bodyStarted = resolve; });
  const body = new Promise(resolve => { resolveBody = resolve; });
  const api = createPythonTablesApi(async () => ({
    ok: true,
    headers: { get: () => 'application/json' },
    json: async () => {
      bodyStarted();
      return body;
    }
  }));
  const pending = api.listTables({ signal: controller.signal });
  await started;
  controller.abort();
  resolveBody({ tables: [{ id: 'synthetic-T1', seats: 4, guests: 2 }] });
  await assert.rejects(pending, { name: 'AbortError' });
});

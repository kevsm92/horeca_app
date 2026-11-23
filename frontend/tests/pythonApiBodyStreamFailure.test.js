import test from 'node:test';
import assert from 'node:assert/strict';
import { createPythonTablesApi, PythonApiError } from '../src/pythonApi.js';

// Synthetic transport responses only; /api/v1/tables is not a verified Python route.
const jsonHeaders = { get: () => 'application/json' };

test('body-stream AbortError is preserved when the request is cancelled', async () => {
  const controller = new AbortController();
  let beginBody;
  const bodyStarted = new Promise(resolve => { beginBody = resolve; });
  const api = createPythonTablesApi(async () => ({
    ok: true,
    headers: jsonHeaders,
    json: async () => {
      beginBody();
      await new Promise((_, reject) => {
        controller.signal.addEventListener('abort', () =>
          reject(new DOMException('Cancelled during JSON read', 'AbortError')), { once: true });
      });
    }
  }));
  const pending = api.listTables({ signal: controller.signal });
  await bodyStarted;
  controller.abort();
  await assert.rejects(pending, error =>
    error.name === 'AbortError' && !(error instanceof PythonApiError));
});

test('uncancelled body-stream failure is reported as invalid JSON, never fallback data', async () => {
  const api = createPythonTablesApi(async () => ({
    ok: true,
    headers: jsonHeaders,
    json: async () => { throw new TypeError('Synthetic stream failure'); }
  }));
  await assert.rejects(api.listTables(), error =>
    error instanceof PythonApiError && error.code === 'INVALID_RESPONSE');
});

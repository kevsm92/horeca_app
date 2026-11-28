import test from 'node:test';
import assert from 'node:assert/strict';
import { createPythonTablesApi, PythonApiError } from '../src/pythonApi.js';

// The tables adapter is dormant until an authenticated Python route is verified.
const reply = (json) => ({
  ok: true, status: 200,
  headers: { get: () => 'application/json; charset=utf-8' }, json
});

test('abort signal reaches browser fetch and abort errors are not rewritten as network failures', async () => {
  const controller = new AbortController();
  const aborted = new DOMException('cancelled', 'AbortError');
  let receivedSignal;
  const api = createPythonTablesApi(async (_url, options) => {
    receivedSignal = options.signal;
    controller.abort();
    throw aborted;
  });
  await assert.rejects(api.listTables({ signal: controller.signal }), error => error === aborted);
  assert.strictEqual(receivedSignal, controller.signal);
});

test('cancellation during JSON body reading retains the abort error', async () => {
  const controller = new AbortController();
  const aborted = new DOMException('body cancelled', 'AbortError');
  const api = createPythonTablesApi(async () => reply(async () => {
    controller.abort();
    throw aborted;
  }));
  await assert.rejects(api.listTables({ signal: controller.signal }), error => error === aborted);
});

test('late successful JSON response is rejected after cancellation instead of exposing stale venue rows', async () => {
  const controller = new AbortController();
  const api = createPythonTablesApi(async () => reply(async () => {
    controller.abort();
    return { tables: [{ id: 'T1', seats: 4, guests: 2 }] };
  }));
  await assert.rejects(api.listTables({ signal: controller.signal }), error =>
    error.name === 'AbortError' && !(error instanceof PythonApiError));
});

import test from 'node:test';
import assert from 'node:assert/strict';
import { createPythonTablesApi } from '../src/pythonApi.js';

// Contract tests for the dormant read-only Python adapter; no live endpoint is assumed.
const response = (json = async () => ({ tables: [{ id: 'T1', seats: 4, guests: 2 }] })) => ({
  ok: true, status: 200, headers: { get: () => 'application/json' }, json
});

test('passes cancellation signal to the Python request and does not relabel aborted fetch as offline', async () => {
  const controller = new AbortController();
  let receivedSignal;
  const api = createPythonTablesApi(async (_url, options) => {
    receivedSignal = options.signal;
    controller.abort();
    throw new DOMException('Cancelled', 'AbortError');
  });
  await assert.rejects(api.listTables({ signal: controller.signal }), error => error.name === 'AbortError');
  assert.equal(receivedSignal, controller.signal);
});

test('aborting while reading JSON preserves AbortError rather than reporting malformed JSON', async () => {
  const controller = new AbortController();
  const api = createPythonTablesApi(async () => response(async () => {
    controller.abort();
    throw new DOMException('Cancelled', 'AbortError');
  }));
  await assert.rejects(api.listTables({ signal: controller.signal }), error => error.name === 'AbortError');
});

test('late successful JSON from a cancelled view never exposes stale venue tables', async () => {
  const controller = new AbortController();
  const api = createPythonTablesApi(async () => response(async () => {
    controller.abort();
    return { tables: [{ id: 'T1', seats: 4, guests: 2 }] };
  }));
  await assert.rejects(api.listTables({ signal: controller.signal }), error => error.name === 'AbortError');
});

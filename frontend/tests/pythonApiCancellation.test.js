import test from 'node:test';
import assert from 'node:assert/strict';
import { createPythonTablesApi, PythonApiError } from '../src/pythonApi.js';

test('read-only Python tables request forwards AbortSignal without initiating another request', async () => {
  const controller = new AbortController();
  let calls = 0;
  const api = createPythonTablesApi(async (url, options) => {
    calls += 1;
    assert.equal(url, '/api/v1/tables');
    assert.equal(options.signal, controller.signal);
    return {
      ok: true,
      headers: { get: () => 'application/json' },
      json: async () => ({ tables: [] })
    };
  });
  assert.deepEqual(await api.listTables({ signal: controller.signal }), []);
  assert.equal(calls, 1);
});

test('aborted Python tables request propagates cancellation rather than misreporting network failure', async () => {
  const controller = new AbortController();
  const abortError = Object.assign(new Error('cancelled'), { name: 'AbortError' });
  const api = createPythonTablesApi(async (_url, { signal }) => {
    assert.equal(signal, controller.signal);
    controller.abort();
    throw abortError;
  });
  await assert.rejects(api.listTables({ signal: controller.signal }), error =>
    error === abortError && !(error instanceof PythonApiError)
  );
});

test('aborted streaming JSON read preserves cancellation instead of malformed-response error', async () => {
  const controller = new AbortController();
  const abortError = Object.assign(new Error('cancelled during body read'), { name: 'AbortError' });
  const api = createPythonTablesApi(async () => ({
    ok: true,
    headers: { get: () => 'application/json' },
    json: async () => {
      controller.abort();
      throw abortError;
    }
  }));
  await assert.rejects(api.listTables({ signal: controller.signal }), error =>
    error === abortError && !(error instanceof PythonApiError)
  );
});

test('late abort discards parsed data rather than exposing a stale venue snapshot', async () => {
  const controller = new AbortController();
  const api = createPythonTablesApi(async () => ({
    ok: true,
    headers: { get: () => 'application/json' },
    json: async () => {
      controller.abort();
      return { tables: [{ id: 'T1', seats: 4, guests: 2 }] };
    }
  }));
  await assert.rejects(api.listTables({ signal: controller.signal }), { name: 'AbortError' });
});

test('pre-aborted view does not issue a Python HTTP request', async () => {
  const controller = new AbortController();
  controller.abort();
  let calls = 0;
  const api = createPythonTablesApi(async () => {
    calls += 1;
    throw new Error('fetch must not be called');
  });
  await assert.rejects(api.listTables({ signal: controller.signal }), { name: 'AbortError' });
  assert.equal(calls, 0);
});

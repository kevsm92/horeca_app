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

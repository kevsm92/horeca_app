import test from 'node:test';
import assert from 'node:assert/strict';
import { createPythonTablesApi, PythonApiError } from '../src/pythonApi.js';

test('cancellation while reading JSON body propagates the original AbortError', async () => {
  const controller = new AbortController();
  const abortError = Object.assign(new Error('cancelled while reading body'), { name: 'AbortError' });
  const api = createPythonTablesApi(async () => ({
    ok: true,
    headers: { get: () => 'application/json; charset=utf-8' },
    async json() { controller.abort(); throw abortError; }
  }));
  await assert.rejects(api.listTables({ signal: controller.signal }), error =>
    error === abortError && !(error instanceof PythonApiError)
  );
});

test('malformed JSON without cancellation remains INVALID_RESPONSE', async () => {
  const controller = new AbortController();
  const api = createPythonTablesApi(async () => ({
    ok: true,
    headers: { get: () => 'application/json' },
    async json() { throw new SyntaxError('unexpected token'); }
  }));
  await assert.rejects(api.listTables({ signal: controller.signal }), error =>
    error instanceof PythonApiError && error.code === 'INVALID_RESPONSE'
  );
  assert.equal(controller.signal.aborted, false);
});

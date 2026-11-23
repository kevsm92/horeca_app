import test from 'node:test';
import assert from 'node:assert/strict';
import { createPythonTablesApi } from '../src/pythonApi.js';

// Synthetic concurrent browser reads; no live Python route is assumed.
test('cancelling one view does not cancel another concurrent tables read', async () => {
  const first = new AbortController();
  const second = new AbortController();
  const requests = [];
  const api = createPythonTablesApi((_url, options) => new Promise((resolve, reject) => {
    requests.push({ signal: options.signal, resolve });
    options.signal.addEventListener('abort', () =>
      reject(new DOMException('View cancelled', 'AbortError')), { once: true });
  }));

  const cancelled = api.listTables({ signal: first.signal });
  const active = api.listTables({ signal: second.signal });
  assert.equal(requests.length, 2);
  assert.equal(requests[0].signal, first.signal);
  assert.equal(requests[1].signal, second.signal);

  first.abort();
  requests[1].resolve({
    ok: true,
    status: 200,
    headers: { get: () => 'application/json' },
    json: async () => ({ tables: [{ id: 'T2', seats: 4, guests: 2 }] })
  });
  await assert.rejects(cancelled, error => error.name === 'AbortError');
  assert.deepEqual(await active, [{ id: 'T2', seats: 4, guests: 2 }]);
  assert.equal(second.signal.aborted, false);
});

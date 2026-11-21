import test from 'node:test';
import assert from 'node:assert/strict';
import { createPythonTablesApi, PythonApiError } from '../src/pythonApi.js';

const response = tables => ({
  ok: true,
  status: 200,
  headers: { get: () => 'application/json' },
  json: async () => ({ tables })
});

test('unauthenticated and forbidden Python responses never become synthetic table data', async () => {
  for (const status of [401, 403]) {
    const api = createPythonTablesApi(async () => ({ ok: false, status }));
    await assert.rejects(api.listTables(), error =>
      error instanceof PythonApiError && error.code === 'HTTP_ERROR' && error.status === status
    );
  }
});

test('concurrent reads return only their own response, regardless of completion order', async () => {
  const resolvers = [];
  const api = createPythonTablesApi(() => new Promise(resolve => resolvers.push(resolve)));
  const first = api.listTables();
  const second = api.listTables();
  assert.equal(resolvers.length, 2);
  resolvers[1](response([{ id: 'B1', seats: 2, guests: 1 }]));
  assert.deepEqual(await second, [{ id: 'B1', seats: 2, guests: 1 }]);
  resolvers[0](response([{ id: 'A1', seats: 4, guests: 3 }]));
  assert.deepEqual(await first, [{ id: 'A1', seats: 4, guests: 3 }]);
});

test('a failed subsequent read never silently reuses a previous venue snapshot', async () => {
  let calls = 0;
  const api = createPythonTablesApi(async () => {
    calls++;
    return calls === 1 ? response([{ id: 'T1', seats: 4, guests: 2 }]) : { ok: false, status: 503 };
  });
  assert.deepEqual(await api.listTables(), [{ id: 'T1', seats: 4, guests: 2 }]);
  await assert.rejects(api.listTables(), error =>
    error instanceof PythonApiError && error.code === 'HTTP_ERROR' && error.status === 503
  );
  assert.equal(calls, 2);
});

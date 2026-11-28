import test from 'node:test';
import assert from 'node:assert/strict';
import { createPythonTablesApi, PythonApiError } from '../src/pythonApi.js';

const reply = (contentType, tables = []) => ({
  ok: true,
  status: 200,
  headers: { get: name => name === 'content-type' ? contentType : null },
  json: async () => ({ tables })
});

test('accepts only the documented JSON media type with optional charset', async () => {
  for (const mediaType of ['application/json', 'application/json; charset=utf-8', 'APPLICATION/JSON; charset=UTF-8']) {
    const api = createPythonTablesApi(async () => reply(mediaType));
    assert.deepEqual(await api.listTables(), []);
  }
});

test('rejects HTML fallbacks, JSON-like and absent content types before parsing', async () => {
  for (const mediaType of ['text/html', 'application/problem+json', 'text/json', 'application/jsonp', '', null]) {
    let parsed = false;
    const api = createPythonTablesApi(async () => ({
      ...reply(mediaType),
      json: async () => { parsed = true; return { tables: [] }; }
    }));
    await assert.rejects(api.listTables(), error =>
      error instanceof PythonApiError && error.code === 'INVALID_RESPONSE'
    );
    assert.equal(parsed, false, `unexpected parsing for ${mediaType}`);
  }
});

test('preserves HTTP status for rate limits, service failures and empty successful responses', async () => {
  for (const status of [429, 500, 503]) {
    const api = createPythonTablesApi(async () => ({ ok: false, status }));
    await assert.rejects(api.listTables(), error =>
      error instanceof PythonApiError && error.code === 'HTTP_ERROR' && error.status === status
    );
  }
  const empty = createPythonTablesApi(async () => ({ ok: true, status: 204, headers: { get: () => null } }));
  await assert.rejects(empty.listTables(), error =>
    error instanceof PythonApiError && error.code === 'INVALID_RESPONSE'
  );
});

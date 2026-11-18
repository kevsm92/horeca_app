/**
 * Read-only adapter contract for a FUTURE authenticated Python HTTP API.
 * The current repository has Python domain prototypes, not a verified HTTP route.
 * Do not call this client in the demo until /api/v1/tables is implemented and secured.
 * Uses browser fetch only; Node.js is never an application backend.
 */
export class PythonApiError extends Error {
  constructor(code, message, status = null) {
    super(message);
    this.name = 'PythonApiError';
    this.code = code;
    this.status = status;
  }
}

export function parsePythonTables(payload) {
  if (!payload || typeof payload !== 'object' || !Array.isArray(payload.tables)) {
    throw new PythonApiError('INVALID_RESPONSE', 'Invalid Python table response.');
  }
  const seen = new Set();
  return payload.tables.map(row => {
    if (!row || typeof row !== 'object' || typeof row.id !== 'string' ||
        !row.id.trim() || seen.has(row.id) || !Number.isInteger(row.seats) ||
        row.seats < 1 || row.seats > 100 || !Number.isInteger(row.guests) ||
        row.guests < 0 || row.guests > row.seats) {
      throw new PythonApiError('INVALID_RESPONSE', 'Invalid Python table response.');
    }
    seen.add(row.id);
    return Object.freeze({ id: row.id, seats: row.seats, guests: row.guests });
  });
}

export function createPythonTablesApi(fetchImpl = globalThis.fetch) {
  if (typeof fetchImpl !== 'function') {
    throw new TypeError('Browser fetch implementation required.');
  }
  return Object.freeze({
    async listTables({ signal } = {}) {
      let response;
      try {
        // Relative URL and same-origin credentials avoid external hosts and leaked tokens.
        response = await fetchImpl('/api/v1/tables', {
          method: 'GET', credentials: 'same-origin',
          headers: { Accept: 'application/json' }, signal
        });
      } catch (error) {
        if (signal?.aborted) throw error;
        throw new PythonApiError('NETWORK_ERROR', 'Python API unavailable.');
      }
      if (!response || !response.ok) {
        throw new PythonApiError('HTTP_ERROR', 'Python API request failed.', response?.status ?? null);
      }
      const contentType = response.headers?.get?.('content-type') || '';
      if (!/^application\/json(?:\s*;|\s*$)/i.test(contentType)) {
        throw new PythonApiError('INVALID_RESPONSE', 'Python API did not return JSON.');
      }
      let payload;
      try {
        payload = await response.json();
      } catch (error) {
        // Aborting while the response body is streaming is not malformed JSON.
        if (signal?.aborted) throw error;
        throw new PythonApiError('INVALID_RESPONSE', 'Python API returned malformed JSON.');
      }
      // A response body may resolve after the caller has cancelled the view.
      // Never surface stale venue data as a successful read.
      if (signal?.aborted) throw new DOMException('The request was aborted.', 'AbortError');
      return parsePythonTables(payload);
    }
  });
}

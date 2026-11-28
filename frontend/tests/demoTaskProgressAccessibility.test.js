import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

const app = readFileSync(new URL('../src/main.jsx', import.meta.url), 'utf8');

test('fictional checklist progress is computed from current state, not stored independently', () => {
  assert.match(app, /tasks\.filter\(t=>t\.done\)\.length\} of \{tasks\.length\} fictional tasks complete/);
  assert.match(app, /<p className="muted" role="status" aria-live="polite" aria-atomic="true">\{tasks\.filter/);
});

test('checklist progress follows existing toggles and reset without backend writes', () => {
  assert.match(app, /setTasks\(old=>toggleDemoTask\(old,i\)\)/);
  assert.match(app, /setTasks\(resetDemoTasks\(\)\)/);
  assert.match(app, /Fictional browser-only checklist\. Not a compliance evidence record\./);
});

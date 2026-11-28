import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
const source = readFileSync(new URL('../src/main.jsx', import.meta.url), 'utf8');

test('POS shows the authenticated Python catalog before the fictional order builder', () => {
  const start = source.indexOf("{page==='Orders / POS'&&<><PythonMenuCatalog/>");
  assert.ok(start >= 0, 'POS must display the Python menu');
  const demo = source.indexOf('<div className="columns">', start);
  assert.ok(demo > start, 'separate demo order builder must follow catalog');
  assert.match(source.slice(start, demo), /read-only/);
  assert.match(source.slice(start, demo), /separate in-memory demo/);
});

test('Food & Menu retains the authenticated catalog and demo checkout is isolated', () => {
  assert.match(source, /\{page==='Food & Menu'&&<PythonMenuCatalog\/>\}/);
  assert.match(source, /No payments or external API calls\.<\/p><\/aside><\/div><\/>\}/);
});

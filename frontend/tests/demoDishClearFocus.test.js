import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const source = readFileSync(new URL('../src/main.jsx', import.meta.url), 'utf8');

// Source-level contract; browser focus behavior requires interactive verification.
test('clearing fictional POS dish search restores focus to the search input', () => {
  assert.match(source, /id="pos-dish-search" type="search"/);
  assert.match(source, /onClick=\{\(\)=>\{setSearch\(''\);document\.getElementById\('pos-dish-search'\)\?\.focus\(\);\}\} aria-label="Clear dish search"/);
});

test('fictional POS dish search preserves keyboard and results accessibility', () => {
  assert.match(source, /htmlFor="pos-dish-search"/);
  assert.match(source, /onKeyDown=\{e=>\{if\(e\.key==='Escape'&&search\)/);
  assert.match(source, /aria-controls="pos-dish-results"/);
  assert.match(source, /id="pos-dish-results"/);
});

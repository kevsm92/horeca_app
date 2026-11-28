import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

// Source-level contract; browser focus behavior still requires interactive validation.
const source = readFileSync(new URL('../src/CatalogPos.jsx', import.meta.url), 'utf8');

test('authenticated POS catalog exposes a keyboard-operable results jump', () => {
  assert.match(source, /const resultsRef=useRef\(null\)/);
  assert.match(source, /onClick=\{\(\)=>resultsRef\.current\?\.focus\(\)\}/);
  assert.match(source, /aria-controls="catalog-pos-results">Jump to catalog products/);
});

test('results focus destination remains labeled and outside normal tab order', () => {
  assert.match(source, /ref=\{resultsRef\} tabIndex=\{-1\} id="catalog-pos-results"/);
  assert.match(source, /role="region" aria-label="Filtered catalog products"/);
  assert.match(source, /No matching venue products/);
});

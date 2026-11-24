import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

const source=readFileSync(new URL('../src/PythonMenuCatalog.jsx',import.meta.url),'utf8');

test('catalog offers explicit keyboard navigation to its results region',()=>{
  assert.match(source,/const resultsRef=useRef\(null\)/);
  assert.match(source,/onClick=\{\(\)=>resultsRef\.current\?\.focus\(\)\}/);
  assert.match(source,/aria-controls="python-menu-results"/);
});

test('catalog results remain programmatically focusable even when empty',()=>{
  assert.match(source,/<div ref=\{resultsRef\} tabIndex=\{-1\} id="python-menu-results"/);
  assert.match(source,/role="region" aria-label="Catalog results"/);
  assert.match(source,/shown\.length===0\?<p>/);
});

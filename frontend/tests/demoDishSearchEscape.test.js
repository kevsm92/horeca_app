import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

const source=readFileSync(new URL('../src/main.jsx',import.meta.url),'utf8');

test('fictional POS dish search supports Escape without swallowing an empty search',()=>{
  const input=source.match(/<input id="pos-dish-search"[\s\S]*?\/>/)?.[0];
  assert.ok(input,'fictional POS dish search input is present');
  assert.match(input,/aria-keyshortcuts="Escape"/);
  assert.match(input,/onKeyDown=\{e=>\{if\(e\.key==='Escape'&&search\)\{e\.preventDefault\(\);setSearch\(''\);\}\}\}/);
  assert.match(input,/aria-controls="pos-dish-results"/);
});

test('fictional POS dish search retains visible clear control and keyboard help',()=>{
  assert.match(source,/Press Escape to clear the dish search\./);
  assert.match(source,/onClick=\{\(\)=>setSearch\(''\)\} aria-label="Clear dish search"/);
  assert.match(source,/aria-describedby="pos-dish-search-help"/);
});

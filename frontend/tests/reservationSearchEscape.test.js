import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

const source=readFileSync(new URL('../src/main.jsx',import.meta.url),'utf8');

test('fictional reservation search offers an Escape shortcut without interfering with empty searches',()=>{
  const field=source.match(/<input id="reservation-search"[\s\S]*?\/>/)?.[0];
  assert.ok(field,'reservation search input is present');
  assert.match(field,/aria-keyshortcuts="Escape"/);
  assert.match(field,/onKeyDown=\{e=>\{if\(e\.key==='Escape'&&reservationSearch\)\{e\.preventDefault\(\);setReservationSearch\(''\);\}\}\}/);
  assert.match(field,/aria-controls="reservation-results"/);
});

test('reservation keyboard shortcut is documented for keyboard users',()=>{
  assert.match(source,/Press Escape to clear the search/);
  assert.match(source,/onClick=\{\(\)=>setReservationSearch\(''\)\} aria-label="Clear reservation search"/);
});

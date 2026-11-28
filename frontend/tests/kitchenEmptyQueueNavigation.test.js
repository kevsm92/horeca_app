import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const source = readFileSync(new URL('../src/main.jsx', import.meta.url), 'utf8');

test('empty New kitchen lane offers an accessible route to the synthetic POS', () => {
  assert.match(source, /status==='New'&&orders\.every\(o=>o\.status!=='New'\)&&<button type="button"/);
  assert.match(source, /Open demo POS to create a fictional ticket<\/button>/);
  assert.match(source, /setPage\('Orders \/ POS'\);setNotice\(''\);/);
});

test('kitchen ticket progression remains fictional and in React memory', () => {
  assert.match(source, /Fictional ticket #/);
  assert.match(source, /setOrders\(old=>old\.map\(/);
  assert.match(source, /Reopen ticket/);
});

import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

const source=readFileSync(new URL('../src/main.jsx',import.meta.url),'utf8');

test('fictional kitchen tickets are explicitly labelled and do not submit to Python',()=>{
  assert.match(source,/Fictional ticket sent\./);
  assert.match(source,/No payments or external API calls\./);
  assert.match(source,/setOrders\(old=>\[\.\.\.old,/);
  assert.match(source,/setOrders\(old=>old\.map\(x=>x\.id===o\.id/);
});

test('kitchen demo has accessible empty-state and progression actions',()=>{
  for(const state of ['New','Preparing','Ready'])assert.ok(source.includes("'"+state+"'"));
  assert.match(source,/aria-label=\{status\+' kitchen tickets'\}/);
  assert.match(source,/aria-label=\{\(status==='New'\?'Start preparing':'Mark ready'\)/);
  assert.match(source,/No ready tickets yet/);
});

import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

const source=readFileSync(new URL('../src/main.jsx',import.meta.url),'utf8');

test('ready demo tickets have an accessible reopen control',()=>{
  assert.match(source,/status==='Preparing'\?'Mark ready':'Reopen'/);
  assert.match(source,/status==='Preparing'\?'Mark ready':'Reopen ticket'/);
  assert.match(source,/aria-label=\{\(status==='New'\?'Start preparing'/);
});

test('reopening is local to fictional React tickets and returns to preparing',()=>{
  assert.match(source,/status==='Preparing'\?'Ready':'Preparing'/);
  assert.match(source,/setOrders\(old=>old\.map\(x=>x\.id===o\.id\?\{\.\.\.x,status:nextStatus\}:x\)\)/);
  assert.match(source,/Fictional ticket #/);
});

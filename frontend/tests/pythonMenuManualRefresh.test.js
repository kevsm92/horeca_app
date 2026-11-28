import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

const source=readFileSync(new URL('../src/PythonMenuCatalog.jsx',import.meta.url),'utf8');

test('manual catalog refresh is offered only after successful loading',()=>{
 assert.match(source,/state\.status==='ready'&&<button[^>]*onClick=\{\(\)=>setRetry\(n=>n\+1\)\}[^>]*>Refresh catalog<\/button>/);
 assert.match(source,/aria-label="Refresh Python menu catalog"/);
});

test('refresh reuses abortable authenticated loader and existing loading/error states',()=>{
 assert.match(source,/useEffect\(\(\)=>\{\s*const controller=new AbortController\(\)/);
 assert.match(source,/loadMenu\(\{signal:controller\.signal\}\)/);
 assert.match(source,/return \(\)=>controller\.abort\(\);\s*\},\[retry\]\)/);
 assert.match(source,/state\.status==='loading'/);
 assert.match(source,/state\.status==='error'/);
 assert.doesNotMatch(source,/setInterval|setTimeout|localStorage|sessionStorage/);
});

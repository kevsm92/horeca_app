import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

const source=readFileSync(new URL('../src/PythonMenuCatalog.jsx',import.meta.url),'utf8');

test('menu search aria-controls target persists for empty and populated results',()=>{
 assert.match(source,/aria-controls="python-menu-results"/);
 assert.equal(source.match(/id="python-menu-results"/g)?.length,1);
 assert.match(source,/<div id="python-menu-results" className=\{shown\.length===0\?'':'dishes'\}/);
 assert.match(source,/\{shown\.length===0\?<p>/);
 assert.match(source,/shown\.map\(item=><article/);
});

test('catalog empty state distinguishes no configured items from filtered no matches',()=>{
 assert.match(source,/state\.items\.length===0\?'No menu items configured for this venue\.':'No matching food or drinks\.'/);
 assert.match(source,/role="status" aria-live="polite" aria-atomic="true"/);
});

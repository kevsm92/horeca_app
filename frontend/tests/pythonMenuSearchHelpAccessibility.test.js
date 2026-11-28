import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

const source=readFileSync(new URL('../src/PythonMenuCatalog.jsx',import.meta.url),'utf8');

test('catalog search exposes discoverable keyboard guidance and current result count',()=>{
 assert.match(source,/id="python-menu-search-help"/);
 assert.match(source,/Press Escape to clear the search\./);
 assert.match(source,/aria-describedby="python-menu-search-help python-menu-result-count"/);
 assert.match(source,/id="python-menu-result-count" role="status" aria-live="polite"/);
});

test('catalog search guidance references mounted elements in ready state',()=>{
 const ready=source.indexOf("{state.status==='ready'&&<>");
 const help=source.indexOf('id="python-menu-search-help"');
 const input=source.indexOf('aria-label="Search catalog"');
 const count=source.indexOf('id="python-menu-result-count"');
 assert.ok(ready>=0 && ready<help && help<input && input<count);
 assert.equal(source.match(/id="python-menu-search-help"/g)?.length,1);
 assert.equal(source.match(/id="python-menu-result-count"/g)?.length,1);
});

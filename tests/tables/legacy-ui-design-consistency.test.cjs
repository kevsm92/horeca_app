'use strict';
const test=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path');
const base=path.join(__dirname,'../../prototypes/tables'),css=fs.readFileSync(path.join(base,'horeca-ui.css'),'utf8');
const pages=[
['2026-11-12-navigation.html','horeca-navigation',['overview-tab','tables-tab','floor','message']],
['2026-11-12-floorplan.html','horeca-floorplan',['overview-tab','tables-tab','floor','seat','guests']],
['2026-11-12-designer-shell.html','horeca-studio',['service-tab','design-tab','designer','service','seat-action','canvas']]];
for(const [file,klass,ids] of pages)test(file+' local theme and controls',()=>{
 const html=fs.readFileSync(path.join(base,file),'utf8');
 assert.ok(html.includes('<body class="horeca-legacy '+klass+'">'));
 assert.ok(html.includes('<link rel="stylesheet" href="horeca-ui.css">'));
 assert.ok(html.includes('<header class="site-header">'));
 for(const id of ids)assert.ok(html.includes('id="'+id+'"'),id);
 assert.doesNotMatch(html,/<script[^>]+src=|https?:\/\/|@import/i);
});
test('reference palette and accessible responsive styling',()=>{
 for(const hex of ['#f5f6fc','#202033','#5b45d9','#eae7ff','#e3e5f0'])assert.ok(css.includes(hex));
 assert.match(css,/:focus-visible/);
 assert.match(css,/@media\s*\(max-width:\s*680px\)/);
 assert.match(css,/\.horeca-legacy\s+\[hidden\]\s*\{\s*display:\s*none\s*!important;?\s*\}/);
 assert.match(css,/\.horeca-legacy\s+button\[aria-current\]/);
 assert.doesNotMatch(css,/@import|url\(|https?:\/\//i);
});
test('latest floor-plan editor remains separate',()=>{
 const html=fs.readFileSync(path.join(base,'2026-11-13-reference-redesign.html'),'utf8');
 assert.ok(html.includes('Restaurant Floor Plan Editor'));
 assert.ok(!html.includes('horeca-ui.css'));
});

'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const html=fs.readFileSync(require('node:path').join(__dirname,'../../prototypes/pos/staff-pos-shell.html'),'utf8');
const ids=['tables','orders','menu','kitchen'];
test('four tab-panel pairs with accessible labels',()=>{
 for(const id of ids){
  assert.match(html,new RegExp('id="tab-'+id+'"[^>]*aria-controls="panel-'+id+'"'));
  assert.match(html,new RegExp('id="panel-'+id+'"[^>]*aria-labelledby="tab-'+id+'"'));
 }
});
test('one initial selected tab and three hidden panels',()=>{
 assert.equal((html.match(/aria-selected="true"/g)||[]).length,1);
 assert.equal((html.match(/role="tabpanel"/g)||[]).length,4);
 assert.equal((html.match(/role="tabpanel"[^>]* hidden/g)||[]).length,3);
});
test('keyboard controls and roving tabindex exist',()=>{
 for(const key of ['ArrowRight','ArrowLeft','Home','End'])assert.ok(html.includes("event.key==='"+key+"'"));
 assert.ok(html.includes("item.setAttribute('aria-selected',String(active))"));
 assert.ok(html.includes('item.tabIndex=active?0:-1'));
});
test('offline, fictional and no network dependencies',()=>{
 assert.match(html,/OFFLINE · SYNTHETIC DATA/);
 assert.doesNotMatch(html,/<script[^>]+src=|fetch\(|XMLHttpRequest|https?:\/\//);
 assert.match(html,/No authentication, live backend, payments/);
});

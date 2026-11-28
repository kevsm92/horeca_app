'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const html=fs.readFileSync(path.join(__dirname,'../../prototypes/tables/2026-11-13-reference-redesign.html'),'utf8');
function section(a,b){const i=html.indexOf(a),j=html.indexOf(b,i+a.length);assert.ok(i>=0&&j>i);return html.slice(i,j);}
test('drag cleanup removes every registered listener and releases pointer capture',()=>{
 const s=section('function cleanupDrag(d){','function endDrag(e){');
 for(const event of ['pointermove','pointerup','pointercancel'])assert.ok(s.includes("removeEventListener('"+event+"'"));
 assert.match(s,/hasPointerCapture\(d\.pointer\).*releasePointerCapture\(d\.pointer\)/);
});
test('pointer up and cancellation use common cleanup',()=>{
 const s=section('function endDrag(e){',"for(const b of document.querySelectorAll('[data-step]')");
 assert.equal((s.match(/cleanupDrag\(d\)/g)||[]).length,2);
 assert.match(s,/revision!==d\.revision/);
 assert.match(s,/revision===d\.revision/);
});
test('storage and venue switches release capture before loading another layout',()=>{
 const storage=section("window.addEventListener('storage'","read();switchTab('properties');render();");
 assert.ok(storage.indexOf('cleanupDrag(pending)')<storage.indexOf('read();render()'));
 const venue=section("$('venue').addEventListener('change'","$('reset').addEventListener");
 assert.ok(venue.indexOf('cleanupDrag(pending)')<venue.indexOf('venue=e.target.value'));
});
test('duplicate drag starts and foreign pointer ends do not disrupt current gesture',()=>{
 const s=section('function startDrag(e){','function cleanupDrag(d){');
 assert.match(s,/if\(e\.button!==0\|\|drag\)return/);
 const ends=section('function endDrag(e){',"for(const b of document.querySelectorAll('[data-step]')");
 assert.equal((ends.match(/drag\.pointer!==e\.pointerId/g)||[]).length,2);
});

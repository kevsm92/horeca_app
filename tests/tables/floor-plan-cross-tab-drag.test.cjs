'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const html=fs.readFileSync(path.join(__dirname,'../../prototypes/tables/2026-11-13-reference-redesign.html'),'utf8');
function block(from,to){const start=html.indexOf(from);assert.notEqual(start,-1);const end=html.indexOf(to,start+from.length);assert.notEqual(end,-1);return html.slice(start,end);}
test('pointer start records revision and pointer identity',()=>{const s=block('function startDrag(e){','function dragMove(e){');assert.match(s,/pointer:e\.pointerId,revision,startX/);});
test('storage update invalidates pending drag before reading newer coordinates',()=>{const s=block("window.addEventListener('storage'",'read();switchTab(');assert.ok(s.indexOf('drag=null')>=0);assert.ok(s.indexOf('drag=null')<s.indexOf('read();render()'));assert.match(s,/removeEventListener\('pointermove',dragMove\)/);});
test('pointercancel cannot restore stale coordinates or foreign pointer',()=>{const s=block('function cancelDrag(e){',"for(const b of document.querySelectorAll('[data-step]')");assert.match(s,/drag\.pointer!==e\.pointerId/);assert.match(s,/revision===d\.revision/);});
test('pointerup cannot persist after layout revision changes',()=>{const s=block('function endDrag(e){','function cancelDrag(e){');assert.match(s,/revision!==d\.revision/);assert.ok(s.indexOf('revision!==d.revision')<s.indexOf("save(expected,'Dragged "));});

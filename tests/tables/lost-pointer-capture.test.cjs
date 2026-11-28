'use strict';
const test=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path');
const html=fs.readFileSync(path.join(__dirname,'../../prototypes/tables/2026-11-13-reference-redesign.html'),'utf8');
function block(start,end){
 const a=html.indexOf(start);assert.ok(a>=0,'missing '+start);
 const b=html.indexOf(end,a+start.length);assert.ok(b>a,'missing '+end);
 return html.slice(a,b);
}
test('drag registers lost capture listener',()=>{
 assert.match(block('function startDrag(e){','function dragMove(e){'),/addEventListener\('lostpointercapture',lostDragCapture,\{once:true\}\)/);
});
test('capture loss cancels, never commits',()=>{
 const s=block('function lostDragCapture(e){','function cancelDrag(e){');
 assert.match(s,/cancelDrag\(e\)/);assert.doesNotMatch(s,/save\(|endDrag\(/);
});
test('cleanup unregisters before releasing capture',()=>{
 const s=block('function cleanupDrag(d){','function endDrag(e){');
 const remove=s.indexOf("removeEventListener('lostpointercapture',lostDragCapture)");
 const release=s.indexOf('releasePointerCapture(d.pointer)');
 assert.ok(remove>=0&&release>remove);
});
test('cancel restores only when revision is unchanged',()=>{
 const s=block('function cancelDrag(e){','for(const b of document.querySelectorAll');
 assert.match(s,/drag=null;cleanupDrag\(d\)/);
 assert.match(s,/if\(revision===d.revision\)positions\[d.id\]=\{x:d.x,y:d.y\}/);
});

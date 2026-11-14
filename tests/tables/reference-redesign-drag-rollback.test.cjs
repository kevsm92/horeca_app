// Exact shipped browser function, offline Node test.
'use strict';
const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const html=fs.readFileSync(path.join(__dirname,'../../prototypes/tables/2026-11-13-reference-redesign.html'),'utf8');
const start=html.indexOf('function endDrag(e){'),end=html.indexOf('\nfunction cancelDrag(',start);
assert.ok(start>=0&&end>start,'extract actual shipped drag handler');
const source=html.slice(start,end);
function run({saveResult=true,revisionAfter=0,changed=true,stale=false}={}){
 const calls=[],positions={T1:{x:changed?36:30,y:40}};
 const context=vm.createContext({positions,revision:0,drag:{id:'T1',pointer:4,x:30,y:40},dragMove:()=>{},
  save:(rev,description)=>{calls.push([rev,description]);if(stale){context.revision=revisionAfter;context.positions={T1:{x:65,y:66}};}return saveResult;},
  render:()=>calls.push('render')});
 const target={removeEventListener:type=>calls.push(type)};
 context.event={pointerId:4,currentTarget:target};
 vm.runInContext(source+'\nendDrag(event)',context,{timeout:1000});
 return {positions:context.positions,calls};
}
test('drag persists changed coordinates',()=>{const r=run();assert.equal(r.positions.T1.x,36);assert.deepEqual(r.calls,[ 'pointermove',[0,'Dragged T1'],'render']);});
test('failed drag storage restores initial coordinates',()=>{const r=run({saveResult:false});assert.equal(r.positions.T1.x,30);assert.equal(r.positions.T1.y,40);});
test('unchanged drag never persists',()=>{const r=run({changed:false});assert.deepEqual(r.calls,['pointermove','render']);});
test('failed stale revision does not overwrite a refreshed layout',()=>{const r=run({saveResult:false,stale:true,revisionAfter:2});assert.equal(r.positions.T1.x,65);});

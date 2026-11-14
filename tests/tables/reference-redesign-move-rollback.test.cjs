// Exact shipped HTML movement regression: run with node --test tests/tables/reference-redesign-move-rollback.test.cjs
'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const html=fs.readFileSync(path.join(__dirname,'../../prototypes/tables/2026-11-13-reference-redesign.html'),'utf8');
const begin=html.indexOf('function move(id,x,y){');
const end=html.indexOf('\nfunction onKey(',begin);
assert.ok(begin>=0&&end>begin,'extract actual browser move function');
const source=html.slice(begin,end);
function run(id,x,y,{saveResult=true,revisionAfterSave=0}={}){
 const positions={T1:{x:18,y:20},T2:{x:50,y:43}};
 const calls=[];
 const context=vm.createContext({positions,revision:0,
  clone:p=>JSON.parse(JSON.stringify(p)),
  save:(expected,action)=>{calls.push([expected,action]);context.revision=revisionAfterSave;return saveResult;},
  render:()=>calls.push('render')});
 const result=new vm.Script(source+`\nmove(${JSON.stringify(id)},${JSON.stringify(x)},${JSON.stringify(y)})`).runInContext(context,{timeout:1000});
 return {result,positions:context.positions,calls};
}
test('successful keyboard-sized movement persists selected table only',()=>{
 const r=run('T2',51,43);
 assert.equal(r.result,true);assert.equal(r.positions.T2.x,51);assert.equal(r.positions.T1.x,18);
 assert.deepEqual(r.calls,[[0,'Moved T2'],'render']);
});
test('storage failure rolls back coordinates without reporting a move',()=>{
 const r=run('T2',51,43,{saveResult:false});
 assert.equal(r.result,false);assert.deepEqual(r.positions.T2,{x:50,y:43});
 assert.deepEqual(r.calls,[[0,'Moved T2'],'render']);
});
test('stale revision does not overwrite latest layout restored by save',()=>{
 const r=run('T2',51,43,{saveResult:false,revisionAfterSave:2});
 assert.equal(r.result,false);assert.equal(r.calls.length,2);
});
test('invalid, absent and unchanged moves never write',()=>{
 for(const [id,x,y] of [['T9',51,43],['T2',NaN,43],['T2',50,43]]){
  const r=run(id,x,y);assert.equal(r.result,false);assert.deepEqual(r.calls,[]);
 }
});
test('movement is bounded and rounded to room percentage precision',()=>{
 const r=run('T2',100,-100);
 assert.equal(r.result,true);assert.equal(r.positions.T2.x,88);assert.equal(r.positions.T2.y,12);
});

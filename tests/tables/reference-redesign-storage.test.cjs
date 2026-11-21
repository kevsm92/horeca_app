// Regression for the exact floor-plan save(expected, action) implementation.
// Run from repository root: node --test tests/tables/reference-redesign-storage.test.cjs
'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const html=fs.readFileSync(path.join(__dirname,'../../prototypes/tables/2026-11-13-reference-redesign.html'),'utf8');
const start=html.indexOf('function save(expected,action){');
const stop=html.indexOf('\nfunction revisionList()',start);
assert.ok(start>=0&&stop>start,'shipped save(expected,action) must exist');
const source=html.slice(start,stop);
const baseline={T1:{x:18,y:20},T2:{x:50,y:43},T3:{x:79,y:21},T4:{x:23,y:77},T5:{x:78,y:78}};
function run(mode){
 let stored=mode==='conflict'?JSON.stringify({revision:2}):null;
 let writes=0,reads=0,renders=0;
 const notices=[],badges=[];
 const context=vm.createContext({
  revision:0,savedAt:'',positions:baseline,history:[],
  localStorage:{getItem(){return stored;},setItem(k,v){writes++;if(mode==='failure')throw Error('QuotaExceededError');stored=v;}},
  key:()=> 'synthetic:VEN-001',clone:p=>JSON.parse(JSON.stringify(p)),
  read(){reads++;},render(){renders++;},announce:s=>notices.push(s),renderSaveBadge:(...args)=>badges.push(args),Date,
 });
 const result=new vm.Script(source+'\nsave(0,"Moved T2")').runInContext(context,{timeout:1000});
 return {result,revision:context.revision,savedAt:context.savedAt,history:context.history,stored,writes,reads,renders,notices,badges};
}
test('success persists one versioned snapshot and advances revision only after write',()=>{
 const r=run('success'),d=JSON.parse(r.stored);
 assert.equal(r.result,true);assert.equal(r.revision,1);assert.equal(r.writes,1);
 assert.equal(d.revision,1);assert.equal(d.history.length,1);
 assert.equal(d.history[0].action,'Moved T2');assert.deepEqual(d.history[0].positions,baseline);
 assert.equal(r.history.length,1);assert.ok(r.savedAt);assert.equal(r.savedAt,d.savedAt);
});
test('quota failure preserves revision, timestamp and in-memory history',()=>{
 const r=run('failure');
 assert.equal(r.result,false);assert.equal(r.revision,0);assert.equal(r.savedAt,'');
 assert.equal(r.history.length,0);assert.equal(r.stored,null);assert.equal(r.writes,1);
 assert.match(r.notices.join(' '),/storage could not be updated/i);
 assert.match(r.badges.map(x=>x[0]).join(' '),/unsaved/i);
});
test('stale revision reloads without writing or incrementing',()=>{
 const r=run('conflict');
 assert.equal(r.result,false);assert.equal(r.revision,0);assert.equal(r.writes,0);
 assert.equal(r.reads,1);assert.equal(r.renders,1);
 assert.equal(JSON.parse(r.stored).revision,2);
 assert.match(r.notices.join(' '),/Conflict/);
});

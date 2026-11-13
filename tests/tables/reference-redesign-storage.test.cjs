// Regression for floor-plan localStorage optimistic revision handling.
// Run: node --test tests/tables/reference-redesign-storage.test.cjs
'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const html=fs.readFileSync(path.join(__dirname,'../../prototypes/tables/2026-11-13-reference-redesign.html'),'utf8');
const start=html.indexOf('function save(expected)');
const stop=html.indexOf('\nfunction render()',start);
assert.ok(start>=0&&stop>start,'shipped save function must exist');
const saveSource=html.slice(start,stop);
function run(mode){
  let stored=mode==='conflict'?JSON.stringify({revision:2}):null;
  const notices=[],badges=[];
  const context=vm.createContext({
    revision:0,savedAt:'',positions:{T2:{x:50,y:43}},
    localStorage:{getItem(){return stored;},setItem(k,v){if(mode==='failure')throw Error('QuotaExceededError');stored=v;}},
    key:()=> 'synthetic:VEN-001',read(){},render(){},announce(s){notices.push(s);},renderSaveBadge(s){badges.push(s);}
  });
  const result=new vm.Script(saveSource+'\nsave(0)').runInContext(context,{timeout:1000});
  return {result,revision:context.revision,savedAt:context.savedAt,stored,notices,badges};
}
test('successful save advances revision after persisted write',()=>{
  const r=run('success');
  assert.equal(r.result,true);
  assert.equal(r.revision,1);
  assert.equal(JSON.parse(r.stored).revision,1);
  assert.ok(r.savedAt);
});
test('quota failure does not claim a persisted revision or timestamp',()=>{
  const r=run('failure');
  assert.equal(r.result,false);
  assert.equal(r.revision,0);
  assert.equal(r.savedAt,'');
  assert.equal(r.stored,null);
  assert.match(r.notices.join(' '),/Could not save/);
  assert.match(r.badges.join(' '),/unsaved/);
});
test('stale revision is rejected without writing or incrementing',()=>{
  const r=run('conflict');
  assert.equal(r.result,false);
  assert.equal(r.revision,0);
  assert.equal(JSON.parse(r.stored).revision,2);
  assert.match(r.notices.join(' '),/Conflict/);
});

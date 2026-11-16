'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const html=fs.readFileSync(require('node:path').join(__dirname,'../../prototypes/pos/staff-pos-shell.html'),'utf8');
const match=html.match(/const demoVenue='bistro-noord-fictional';([\s\S]*?)function renderDemoTables\(/);
if(!match)throw new Error('Offline seating domain logic missing');
function fixture(){
 const sandbox={};
 const physical=match[1].match(/const physicalTables=\[[\s\S]*?\];/);
 const seating=match[1].match(/function seatDemoTable\([\s\S]*?\n}/);
 if(!physical||!seating)throw new Error('Seating implementation not found');
 vm.runInNewContext("const demoVenue='bistro-noord-fictional';"+physical[0]+seating[0]+";globalThis.seatDemoTable=seatDemoTable;globalThis.physicalTables=physicalTables;",sandbox,{timeout:1000});
 return sandbox;
}
test('valid seating changes one available physical table',()=>{
 const s=fixture();assert.equal(s.seatDemoTable('T1',2).ok,true);assert.equal(s.physicalTables[0].guests,2);
});
test('physical capacity cannot be exceeded',()=>{
 const s=fixture();assert.equal(s.seatDemoTable('T1',3).ok,false);assert.equal(s.physicalTables[0].guests,0);
});
test('occupied table cannot be seated twice',()=>{
 const s=fixture();assert.equal(s.seatDemoTable('T3',1).ok,false);assert.equal(s.physicalTables[2].guests,3);
 assert.equal(s.seatDemoTable('T2',2).ok,true);assert.equal(s.seatDemoTable('T2',1).ok,false);
});
test('venue isolation and missing table fail closed',()=>{
 const s=fixture();assert.equal(s.seatDemoTable('T1',1,'other-venue').ok,false);
 assert.equal(s.seatDemoTable('T999',1).ok,false);assert.equal(s.physicalTables[0].guests,0);
});
test('invalid fractional, negative, zero and nonnumeric guest counts fail closed',()=>{
 const s=fixture();for(const n of [0,-1,1.5,'abc','',Infinity])assert.equal(s.seatDemoTable('T1',n).ok,false);
 assert.equal(s.physicalTables[0].guests,0);
});
test('no network, persistence or real guest collection in prototype',()=>{
 assert.doesNotMatch(html,/fetch\(|XMLHttpRequest|localStorage|sessionStorage|<form[^>]+action=/);
 assert.match(html,/Offline seating simulation/);
});

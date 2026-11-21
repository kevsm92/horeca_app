'use strict';
// Synthetic-only lifecycle regression against the shipped offline Tables prototype.
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const html = fs.readFileSync(path.resolve(__dirname, '../../prototypes/tables/2026-11-12-designer-shell.html'), 'utf8');
const script = html.match(/<script>([\s\S]*?)<\/script>/);
assert.ok(script);
const boundary = script[1].indexOf('for(const name of templates)');
assert.ok(boundary > 0);
function fixture(){
 const context=vm.createContext({Map,Number,Object,Array});
 vm.runInContext(script[1].slice(0,boundary)+'\nglobalThis.api={seatMock,serviceSessions,tables};',context,{timeout:1000});
 return context.api;
}
test('ending a fictional seating session releases the physical table for reseating',()=>{
 const {seatMock,serviceSessions}=fixture();
 assert.match(seatMock('T01',2),/accepted/);
 assert.equal(serviceSessions.delete('T01'),true);
 assert.match(seatMock('T01',1),/accepted/);
 assert.equal(serviceSessions.get('T01'),1);
});
test('ending one session does not release another occupied table',()=>{
 const {seatMock,serviceSessions}=fixture();
 seatMock('T01',2);seatMock('T02',3);
 assert.equal(serviceSessions.delete('T01'),true);
 assert.match(seatMock('T02',1),/already occupied/);
 assert.equal(serviceSessions.get('T02'),3);
});
test('invalid seating attempts cannot overwrite an active session',()=>{
 const {seatMock,serviceSessions}=fixture();
 seatMock('T03',4);
 for(const guests of [0,-1,2.5,7,NaN,Infinity]) assert.match(seatMock('T03',guests),/Rejected/);
 assert.equal(serviceSessions.get('T03'),4);
});
test('unknown table cannot create or end a fictional session',()=>{
 const {seatMock,serviceSessions}=fixture();
 assert.match(seatMock('UNLISTED',1),/not found/);
 assert.equal(serviceSessions.delete('UNLISTED'),false);
 assert.equal(serviceSessions.size,0);
});

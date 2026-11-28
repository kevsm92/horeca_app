// Offline regression tests for the fictional Tables Service prototype.
// Run: node --test tests/tables/designer-seat-mock.test.cjs
// No network, dependencies, customer data, or production seating.
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const html = fs.readFileSync(path.resolve(__dirname, '../../prototypes/tables/2026-11-12-designer-shell.html'), 'utf8');
const match = html.match(/<script>([\s\S]*?)<\/script>/);
assert.ok(match, 'designer HTML must contain its inline script');
// Evaluate the actual shipped logic up to UI event registration, not a copy
// of seatMock. The only omitted code is browser DOM initialization.
const marker = 'for(const name of templates)';
const end = match[1].indexOf(marker);
assert.ok(end > 0, 'UI initialization marker must remain identifiable');
const logic = match[1].slice(0, end);
function fixture() {
  const context = vm.createContext({ Map, Number, Object, Array });
  vm.runInContext(logic + '\n globalThis.testAPI = { seatMock, serviceSessions, tables };', context, { timeout: 1000 });
  return context.testAPI;
}
test('valid seating records one fictional session', () => {
  const {seatMock, serviceSessions} = fixture();
  assert.match(seatMock('T01', 2), /accepted/);
  assert.equal(serviceSessions.get('T01'), 2);
});
test('same physical table cannot be seated twice', () => {
  const {seatMock, serviceSessions} = fixture();
  seatMock('T01', 1);
  assert.match(seatMock('T01', 1), /already occupied/);
  assert.equal(serviceSessions.size, 1);
});
test('reject capacity overflow without mutation', () => {
  const {seatMock, serviceSessions} = fixture();
  assert.match(seatMock('T02', 5), /exceeds physical seating capacity/);
  assert.equal(serviceSessions.size, 0);
});
test('reject unknown physical table', () => {
  const {seatMock, serviceSessions} = fixture();
  assert.match(seatMock('OTHER-VENUE', 1), /not found/);
  assert.equal(serviceSessions.size, 0);
});
for (const [name, guests] of [['zero', 0], ['negative', -1], ['fractional', 1.5], ['NaN', NaN], ['infinite', Infinity], ['unsafe integer', Number.MAX_SAFE_INTEGER + 1]]) {
  test('reject ' + name + ' guest count without mutation', () => {
    const {seatMock, serviceSessions} = fixture();
    assert.match(seatMock('T03', guests), /positive whole guest count/);
    assert.equal(serviceSessions.size, 0);
  });
}
test('accepted guest count equals physical table limit', () => {
  const {seatMock, serviceSessions} = fixture();
  assert.match(seatMock('T03', 6), /accepted/);
  assert.equal(serviceSessions.get('T03'), 6);
});
test('every inventory ID is unique and capacities positive integers', () => {
  const {tables} = fixture();
  assert.equal(new Set(tables.map(t => t.id)).size, tables.length);
  for (const t of tables) assert.ok(Number.isSafeInteger(t.seats) && t.seats > 0);
});

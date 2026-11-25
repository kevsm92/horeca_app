import test from 'node:test';
import assert from 'node:assert/strict';
import {demoReservations,filterDemoReservations} from '../src/demoReservations.js';

test('fictional reservation search matches accent-insensitive, reordered terms across fields',()=>{
  const rows=Object.freeze([
    Object.freeze({id:'r1',name:'Élodie Noël',table:'T7',time:'19:30'}),
    Object.freeze({id:'r2',name:'Jamie Lee',table:'T2',time:'20:00'})
  ]);
  assert.deepEqual(filterDemoReservations(rows,'t7 ÉLODIE'),[rows[0]]);
  assert.deepEqual(filterDemoReservations(rows,'19 30 noel'),[rows[0]]);
  assert.deepEqual(filterDemoReservations(rows,'20:00 lee'),[rows[1]]);
  assert.deepEqual(filterDemoReservations(rows,'unknown'),[]);
});

test('empty or punctuation-only queries preserve source order without mutating frozen demo records',()=>{
  const all=filterDemoReservations(demoReservations,'  !!!  ');
  assert.deepEqual(all,demoReservations);
  assert.notStrictEqual(all,demoReservations);
  assert.deepEqual(filterDemoReservations(demoReservations,'   '),demoReservations);
  assert.ok(Object.isFrozen(demoReservations));
  assert.ok(demoReservations.every(Object.isFrozen));
});

import test from 'node:test';
import assert from 'node:assert/strict';
import {filterDemoReservations} from '../src/demoReservations.js';

// Fictional records only. Compatibility normalization is a browser search convenience.
const rows = Object.freeze([
  Object.freeze({id:'r1',name:'Ａｌｅｘ Morgan',table:'Ｔ１',time:'１９:３０'}),
  Object.freeze({id:'r2',name:'Jamie Lee',table:'T2',time:'20:00'})
]);

test('full-width guest, table and time text match ordinary Latin queries', () => {
  assert.deepEqual(filterDemoReservations(rows,'alex t1 19:30'),[rows[0]]);
  assert.deepEqual(filterDemoReservations(rows,'ＡＬＥＸ Ｔ１'),[rows[0]]);
  assert.deepEqual(filterDemoReservations(rows,'jamie 20:00'),[rows[1]]);
});

test('compatibility search preserves immutable source records and ordering', () => {
  const before=JSON.stringify(rows);
  assert.deepEqual(filterDemoReservations(rows,''),[...rows]);
  assert.deepEqual(filterDemoReservations(rows,'t1 jamie'),[]);
  assert.equal(JSON.stringify(rows),before);
});

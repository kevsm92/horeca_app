import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const source = readFileSync(new URL('../src/main.jsx', import.meta.url), 'utf8');

test('demo search inputs have independent React focus refs', () => {
  assert.match(source, /const reservationSearchRef=useRef\(null\)/);
  assert.match(source, /const demoDishSearchRef=useRef\(null\)/);
  assert.match(source, /id="reservation-search" ref=\{reservationSearchRef\}/);
  assert.match(source, /id="pos-dish-search" ref=\{demoDishSearchRef\}/);
});

test('clear buttons focus their own input without global DOM lookup', () => {
  assert.match(source, /setReservationSearch\(''\);reservationSearchRef\.current\?\.focus\(\)/);
  assert.match(source, /setSearch\(''\);demoDishSearchRef\.current\?\.focus\(\)/);
  assert.doesNotMatch(source, /document\.getElementById\('(reservation-search|pos-dish-search)'\)/);
});

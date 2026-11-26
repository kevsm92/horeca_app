import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const source = readFileSync(new URL('../src/main.jsx', import.meta.url), 'utf8');

// Source-level accessibility contract; browser focus behavior still needs interactive testing.
test('clearing demo reservation search restores focus before removing the clear control', () => {
  assert.match(source, /onClick=\\{\\(\\)=>\\{setReservationSearch\\(''\\);document\\.getElementById\\('reservation-search'\\)\\?\\.focus\\(\\);\\}\\} aria-label="Clear reservation search"/);
});

test('reservation search retains keyboard Escape and an associated label', () => {
  assert.match(source, /<label htmlFor="reservation-search">Search demo reservations<\\/label>/);
  assert.match(source, /onKeyDown=\\{e=>\\{if\\(e\\.key==='Escape'&&reservationSearch\\)/);
  assert.match(source, /aria-controls="reservation-results"/);
});

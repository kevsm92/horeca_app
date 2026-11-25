import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

// Source-level regression guard for the synthetic SPA's keyboard and screen-reader affordances.
// These checks are not a substitute for interactive browser accessibility testing.
const source = readFileSync(new URL('../src/main.jsx', import.meta.url), 'utf8');

test('demo SPA exposes skip navigation, labeled landmarks and current page', () => {
  assert.match(source, /className="skip-link" href="#main-content"/);
  assert.match(source, /<main id="main-content" ref=\{mainRef\} tabIndex=\{-1\}/);
  assert.match(source, /<nav aria-label="Main navigation"/);
  assert.match(source, /aria-current=\{page===s\?'page':undefined\}/);
});

test('demo floor plan supports keyboard movement and announces changes', () => {
  assert.match(source, /import \{keyboardFloorMove\} from '\.\/floorKeyboardMove\.js';/);
  assert.match(source, /keyboardFloorMove\(floorPositions,id,event\.key,event\.shiftKey,event\)/);
  assert.match(source, /onKeyDown=\{e=>onFloorKeyDown\(e,t\.id\)\}/);
  assert.match(source, /aria-keyshortcuts="ArrowUp ArrowDown ArrowLeft ArrowRight Shift\+ArrowUp/);
  assert.match(source, /setFloorAnnouncement\(result\.announcement\)/);
  assert.match(source, /aria-live="polite">\{floorAnnouncement\}/);
});

test('synthetic POS and reservations communicate filtered results to assistive technology', () => {
  assert.match(source, /aria-controls="pos-dish-results"/);
  assert.match(source, /aria-controls="reservation-results"/);
  assert.match(source, /\{visibleFood\.length\} of \{food\.length\} fictional dishes shown/);
  assert.match(source, /\{visibleReservations\.length\} of \{demoReservations\.length\} fictional reservations shown/);
  assert.match(source, /aria-label="Clear dish search"/);
  assert.match(source, /aria-label="Clear reservation search"/);
});

test('SPA page transitions focus main without stealing initial focus', () => {
  assert.match(source, /const mainRef=useRef\(null\)/);
  assert.match(source, /const initialPageRef=useRef\(true\)/);
  assert.match(source, /if\(initialPageRef\.current\)\{initialPageRef\.current=false;return;\}/);
  assert.match(source, /mainRef\.current\?\.focus\(\)/);
  assert.match(source, /\},\[page\]\)/);
});

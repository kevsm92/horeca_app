import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const app = readFileSync(new URL('../src/main.jsx', import.meta.url), 'utf8');
const css = readFileSync(new URL('../src/styles.css', import.meta.url), 'utf8');

test('SPA navigation and skip link target a programmatically focusable main region', () => {
  assert.match(app, /href="#main-content"/);
  assert.match(app, /<main id="main-content" ref=\{mainRef\} tabIndex=\{-1\}/);
  assert.match(app, /mainRef\.current\?\.focus\(\)/);
  assert.match(app, /\},\[page\]\)/);
  assert.match(css, /main:focus\s*\{[^}]*outline\s*:/);
});

test('keyboard result jumps have real targets and visible focus, including high contrast', () => {
  for (const [id, ref] of [
    ['reservation-results', 'reservationResultsRef'],
    ['pos-dish-results', 'demoDishResultsRef'],
  ]) {
    assert.ok(app.includes('id="'+id+'" ref={'+ref+'} tabIndex={-1}'), id+' focus target');
    assert.ok(app.includes(ref+'.current?.focus()'), id+' jump action');
    assert.match(css, new RegExp('#'+id+':focus\\s*\\{[^}]*outline\\s*:'));
    assert.match(css, new RegExp('@media \\(forced-colors:active\\)\\s*\\{\\s*#'+id+':focus\\s*\\{[^}]*outline-color\\s*:\\s*Highlight'));
  }
});

test('navigation and results do not add unnecessary positive tab stops', () => {
  assert.doesNotMatch(app, /tabIndex=\{[1-9]\d*\}/);
});

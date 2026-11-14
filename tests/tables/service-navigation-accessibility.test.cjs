// Offline structural regression gate for Tables Service navigation and feedback.
// Run: node --test tests/tables/service-navigation-accessibility.test.cjs
// Structural only: browser keyboard and screen-reader behavior require separate tests.
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const html = fs.readFileSync(path.resolve(__dirname, '../../prototypes/tables/2026-11-12-designer-shell.html'), 'utf8');
const checks = [
  ['separate service and designer navigation', /id="service-tab"/.test(html) && /id="design-tab"/.test(html)],
  ['service controls have explicit labels', /for="service-table"/.test(html) && /for="service-guests"/.test(html)],
  ['seating feedback is a polite live status', /id="service-feedback"[^>]*role="status"[^>]*aria-live="polite"/.test(html)],
  ['occupancy reads session state', /serviceSessions\.get\(t\.id\)/.test(html)],
  ['duplicate seating has a state guard', /serviceSessions\.has\(id\)/.test(html)],
  ['ending a simulated session clears its state', /serviceSessions\.delete\(id\)/.test(html)],
  ['prototype has no network transport', !/fetch\s*\(|XMLHttpRequest|WebSocket|sendBeacon/.test(html)],
  ['simulation is explicitly labeled offline', /offline simulation/.test(html)],
];
for (const [name, result] of checks) test(name, () => assert.equal(result, true));

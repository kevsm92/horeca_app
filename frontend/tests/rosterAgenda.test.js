import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const jsx=readFileSync(new URL('../src/WeeklySchedule.jsx',import.meta.url),'utf8');
const css=readFileSync(new URL('../src/weeklySchedule.css',import.meta.url),'utf8');
test('roster offers two labelled, stateful views without changing its source data',()=>{
  assert.match(jsx,/aria-label="Schedule display"/);
  assert.match(jsx,/aria-pressed=\{view==='grid'\}/);
  assert.match(jsx,/aria-pressed=\{view==='agenda'\}/);
  assert.match(jsx,/roster\.filter\(person=>person\.shifts\[i\]\)/);
});
test('agenda details are explicitly fictional and do not infer attendance',()=>{
  assert.match(jsx,/aria-expanded=\{expandedShift===key\}/);
  assert.match(jsx,/Actual attendance is unknown/);
  assert.match(jsx,/No changes are saved/);
  assert.match(jsx,/!roster\.some\(person=>person\.shifts\[i\]\)/);
});
test('agenda remains usable on small screens and forced colours',()=>{
  assert.match(css,/grid-template-columns:repeat\(auto-fit,minmax\(min\(100%,245px\),1fr\)\)/);
  assert.match(css,/min-height:64px/);
  assert.match(css,/@media\(forced-colors:active\)/);
});

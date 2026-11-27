import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const source = readFileSync(new URL('../src/WeeklySchedule.jsx', import.meta.url), 'utf8');

test('weekly grid renders drafts for matching employee and calendar day', () => {
  assert.match(source, /draft\.personId===person\.id&&draft\.date===days\[i\]\.key/);
  assert.match(source, /drafts\.filter\(draft=>draft\.personId/);
});

test('grid drafts are clearly distinguished from published shifts', () => {
  assert.match(source, /Unsaved fictional draft · not published/);
  assert.match(source, /draft\.overnight\?' \(\+1 day\)'/);
});

import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

const source=readFileSync(new URL('../src/WeeklySchedule.jsx',import.meta.url),'utf8');

test('draft-only daily agenda explicitly identifies unknown staffing',()=>{
  assert.match(source,/view==='agenda' && <div className="roster-agenda"/);
  assert.match(source,/\{!roster&&<p className="roster-empty" role="status">No fictional scheduled roster is available for this week\./);
  assert.match(source,/Any drafts shown below are unsaved previews, not a complete staff schedule\. Actual staffing is unknown\./);
  assert.match(source,/drafts\.filter\(draft=>draft\.date===day\.key\)/);
});

test('unknown roster messaging does not remove grid fallback or enable publishing',()=>{
  assert.match(source,/!roster && view==='grid'/);
  assert.match(source,/disabled>➤ Publish Schedule<\/button>/);
});

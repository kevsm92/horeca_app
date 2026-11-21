import test from 'node:test';
import assert from 'node:assert/strict';
import { moveTable } from '../src/floorLayout.js';

// Visual-only synthetic floor geometry. Python owns physical capacity and seating.
const layout = Object.freeze({
  T1: Object.freeze({ x: 20, y: 20 }),
  T2: Object.freeze({ x: 50, y: 50 })
});

test('floor visual overlap is rejected on both axes without mutating the layout', () => {
  for (const [x, y] of [[39, 39], [50, 39], [39, 50], [61, 61]]) {
    assert.strictEqual(moveTable(layout, 'T1', x, y), layout);
  }
  assert.deepEqual(layout.T1, { x: 20, y: 20 });
  assert.deepEqual(layout.T2, { x: 50, y: 50 });
});

test('visual spacing accepts exactly twelve units on either axis', () => {
  for (const [x, y] of [[38, 50], [62, 50], [50, 38], [50, 62]]) {
    const result = moveTable(layout, 'T1', x, y);
    assert.notStrictEqual(result, layout);
    assert.deepEqual(result.T1, { x, y });
    assert.strictEqual(result.T2, layout.T2);
  }
});

test('clamping happens before collision detection', () => {
  const edge = Object.freeze({ T1: Object.freeze({ x: 30, y: 30 }), T2: Object.freeze({ x: 10, y: 10 }) });
  assert.strictEqual(moveTable(edge, 'T1', -100, -100), edge);
  assert.deepEqual(edge.T1, { x: 30, y: 30 });
});

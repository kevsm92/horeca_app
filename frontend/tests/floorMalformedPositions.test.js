import test from 'node:test';
import assert from 'node:assert/strict';
import { moveTable } from '../src/floorLayout.js';

test('malformed synthetic layout inputs are ignored without throwing', () => {
  assert.equal(moveTable(null, 'T1', 40, 40), null);
  assert.equal(moveTable(undefined, 'T1', 40, 40), undefined);
  for (const point of [null, undefined, { x: NaN, y: 20 }, { x: 20, y: Infinity }]) {
    const positions = { T1: point };
    assert.strictEqual(moveTable(positions, 'T1', 30, 30), positions);
  }
});

test('malformed neighbors do not crash visual movement or cause false collisions', () => {
  const positions = Object.freeze({ T1: Object.freeze({ x: 20, y: 20 }), T2: null, T3: { x: NaN, y: 20 }, T4: { x: 60, y: 60 } });
  const next = moveTable(positions, 'T1', 30, 20);
  assert.deepEqual(next.T1, { x: 30, y: 20 });
  assert.strictEqual(next.T2, positions.T2);
  assert.strictEqual(next.T3, positions.T3);
  assert.strictEqual(next.T4, positions.T4);
  assert.strictEqual(moveTable(positions, 'T1', 60, 60), positions);
});

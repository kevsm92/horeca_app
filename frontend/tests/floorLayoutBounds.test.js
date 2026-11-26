import test from 'node:test';
import assert from 'node:assert/strict';
import { moveTable } from '../src/floorLayout.js';

// Visual editor bounds only; real seating and physical capacity remain Python-owned.
test('demo floor clamps finite out-of-bounds pointer positions without mutating frozen inputs', () => {
  const positions = Object.freeze({ T1: Object.freeze({ x: 50, y: 50 }) });
  for (const [x, y, expected] of [
    [-100, -100, { x: 10, y: 10 }],
    [1000, 1000, { x: 90, y: 90 }],
    [-100, 1000, { x: 10, y: 90 }],
    [1000, -100, { x: 90, y: 10 }],
  ]) {
    const result = moveTable(positions, 'T1', x, y);
    assert.deepEqual(result.T1, expected);
    assert.deepEqual(positions.T1, { x: 50, y: 50 });
  }
});

test('demo floor checks collisions after clamping and preserves identity on no-op', () => {
  const positions = Object.freeze({
    T1: Object.freeze({ x: 50, y: 50 }),
    T2: Object.freeze({ x: 10, y: 10 }),
  });
  assert.strictEqual(moveTable(positions, 'T1', -100, -100), positions);
  assert.strictEqual(moveTable(positions, 'T1', 50, 50), positions);
  assert.strictEqual(moveTable(positions, 'missing', 30, 30), positions);
  const moved = moveTable(positions, 'T1', 1000, 1000);
  assert.deepEqual(moved.T1, { x: 90, y: 90 });
  assert.strictEqual(moved.T2, positions.T2);
});

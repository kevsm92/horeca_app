import test from 'node:test';
import assert from 'node:assert/strict';
import { pointerFloorPosition } from '../src/pointerFloorPosition.js';

// Browser-only visual geometry; no occupancy, authorization, or Python writes.
test('pointer geometry rejects missing and non-finite inputs without throwing', () => {
  const origin = Object.freeze({ x: 30, y: 40 });
  const start = Object.freeze({ x: 10, y: 20 });
  const current = Object.freeze({ x: 25, y: 30 });
  const bounds = Object.freeze({ width: 300, height: 200 });
  for (const input of [null, undefined]) {
    assert.equal(pointerFloorPosition(input, start, current, bounds), null);
    assert.equal(pointerFloorPosition(origin, input, current, bounds), null);
    assert.equal(pointerFloorPosition(origin, start, input, bounds), null);
    assert.equal(pointerFloorPosition(origin, start, current, input), null);
  }
  for (const invalid of [NaN, Infinity, -Infinity, undefined, '20']) {
    assert.equal(pointerFloorPosition({ ...origin, x: invalid }, start, current, bounds), null);
    assert.equal(pointerFloorPosition(origin, start, { ...current, y: invalid }, bounds), null);
    assert.equal(pointerFloorPosition(origin, start, current, { ...bounds, width: invalid }), null);
  }
  for (const invalid of [0, -1]) {
    assert.equal(pointerFloorPosition(origin, start, current, { ...bounds, width: invalid }), null);
    assert.equal(pointerFloorPosition(origin, start, current, { ...bounds, height: invalid }), null);
  }
});

test('pointer geometry preserves signed fractional displacement and does not mutate inputs', () => {
  const origin = Object.freeze({ x: 40.5, y: 60.25 });
  const start = Object.freeze({ x: 200, y: 100 });
  const current = Object.freeze({ x: 170, y: 140 });
  const bounds = Object.freeze({ width: 600, height: 400 });
  assert.deepEqual(pointerFloorPosition(origin, start, current, bounds), { x: 35.5, y: 70.25 });
  assert.deepEqual(origin, { x: 40.5, y: 60.25 });
  assert.deepEqual(start, { x: 200, y: 100 });
  assert.deepEqual(current, { x: 170, y: 140 });
});

test('pointer geometry rejects arithmetic overflow even with finite inputs', () => {
  assert.equal(pointerFloorPosition({ x: 20, y: 20 }, { x: -1e308, y: 0 },
    { x: 1e308, y: 0 }, { width: 100, height: 100 }), null);
});

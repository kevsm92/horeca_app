import test from 'node:test';
import assert from 'node:assert/strict';
import { pointerFloorPosition } from '../src/pointerFloorPosition.js';

// Synthetic pointer geometry only; no venue, seating, or persistence operations.
const origin = Object.freeze({ x: 40, y: 60 });
const start = Object.freeze({ x: 100, y: 200 });
const bounds = Object.freeze({ width: 400, height: 200 });

test('pointer movement uses independent horizontal and vertical floor percentages', () => {
  assert.deepEqual(pointerFloorPosition(origin, start, { x: 140, y: 180 }, bounds), { x: 50, y: 50 });
  assert.deepEqual(origin, { x: 40, y: 60 });
});

test('stationary pointer leaves the origin unchanged without mutating inputs', () => {
  assert.deepEqual(pointerFloorPosition(origin, start, start, bounds), origin);
  assert.deepEqual(start, { x: 100, y: 200 });
});

test('zero, negative, or nonfinite floor dimensions are rejected', () => {
  for (const width of [0, -1, NaN, Infinity]) {
    assert.equal(pointerFloorPosition(origin, start, start, { width, height: 200 }), null);
  }
  for (const height of [0, -1, NaN, Infinity]) {
    assert.equal(pointerFloorPosition(origin, start, start, { width: 400, height }), null);
  }
});

test('missing and nonfinite pointer coordinates are rejected', () => {
  assert.equal(pointerFloorPosition(origin, null, start, bounds), null);
  assert.equal(pointerFloorPosition(origin, start, { x: Infinity, y: 0 }, bounds), null);
  assert.equal(pointerFloorPosition({ x: NaN, y: 60 }, start, start, bounds), null);
});

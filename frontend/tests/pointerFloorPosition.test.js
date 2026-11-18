import test from 'node:test';
import assert from 'node:assert/strict';
import { pointerFloorPosition } from '../src/pointerFloorPosition.js';

test('converts pointer movement to floor percentages without mutating origin', () => {
  const origin = Object.freeze({ x: 20, y: 40 });
  assert.deepEqual(pointerFloorPosition(origin, { x: 100, y: 200 }, { x: 150, y: 180 }, { width: 500, height: 200 }), { x: 30, y: 30 });
  assert.deepEqual(origin, { x: 20, y: 40 });
});

test('rejects zero-sized floor during responsive layout transitions', () => {
  assert.equal(pointerFloorPosition({ x: 20, y: 20 }, { x: 0, y: 0 }, { x: 1, y: 1 }, { width: 0, height: 100 }), null);
  assert.equal(pointerFloorPosition({ x: 20, y: 20 }, { x: 0, y: 0 }, { x: 1, y: 1 }, { width: 100, height: -1 }), null);
});

test('rejects nonfinite coordinates and missing geometry', () => {
  assert.equal(pointerFloorPosition({ x: 20, y: 20 }, { x: 0, y: 0 }, { x: Infinity, y: 1 }, { width: 100, height: 100 }), null);
  assert.equal(pointerFloorPosition(null, { x: 0, y: 0 }, { x: 1, y: 1 }, { width: 100, height: 100 }), null);
});

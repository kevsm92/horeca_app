import test from 'node:test';
import assert from 'node:assert/strict';
import {initialFloorPositions, moveTable} from '../src/floorLayout.js';

// Browser-only visual geometry; this does not validate physical seating or write to Python.
test('every synthetic table begins inside the visible floor and has a unique location', () => {
  const entries = Object.entries(initialFloorPositions);
  assert.equal(entries.length, 8);
  const coordinates = new Set();
  for (const [id, point] of entries) {
    assert.match(id, /^T[1-8]$/);
    assert.ok(point.x >= 10 && point.x <= 90);
    assert.ok(point.y >= 10 && point.y <= 90);
    const key = point.x + ',' + point.y;
    assert.equal(coordinates.has(key), false, 'overlapping initial table: ' + id);
    coordinates.add(key);
  }
});

test('unknown and inherited table identifiers cannot create or alter layout entries', () => {
  const original = initialFloorPositions;
  for (const id of ['T0', 'T9', '__proto__', 'constructor', 'toString']) {
    assert.equal(moveTable(original, id, 30, 40), original);
  }
  assert.equal(Object.prototype.hasOwnProperty.call(original, '__proto__'), false);
});

test('moving one table returns a new layout but preserves every other point reference', () => {
  const original = initialFloorPositions;
  const moved = moveTable(original, 'T4', 30, 40);
  assert.notEqual(moved, original);
  assert.deepEqual(moved.T4, {x:30, y:40});
  for (const id of Object.keys(original).filter(id => id !== 'T4')) {
    assert.equal(moved[id], original[id]);
  }
  assert.deepEqual(original.T4, {x:20, y:49});
  assert.equal(moveTable(moved, 'T4', 30, 40), moved);
});

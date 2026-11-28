import test from 'node:test';
import assert from 'node:assert/strict';
import { chairPositions } from '../src/chairPositions.js';

// Presentation-only geometry: chair counts must never authorize actual seating.
test('every supported decorative capacity distributes seats evenly across sides', () => {
  for (let capacity = 1; capacity <= 30; capacity++) {
    const chairs = chairPositions(capacity);
    assert.equal(chairs.length, capacity);
    const counts = ['top', 'right', 'bottom', 'left'].map(side => chairs.filter(chair => chair.side === side).length);
    assert.ok(Math.max(...counts) - Math.min(...counts) <= 1, `unbalanced sides at ${capacity}`);
    for (const side of ['top', 'right', 'bottom', 'left']) {
      const offsets = chairs.filter(chair => chair.side === side).map(chair => chair.offset);
      assert.deepEqual(offsets, [...offsets].sort((a, b) => a - b));
      assert.equal(new Set(offsets).size, offsets.length, `overlapping chairs on ${side} at ${capacity}`);
      for (let i = 0; i < offsets.length; i++) {
        assert.ok(Math.abs(offsets[i] - (i + 1) * 100 / (offsets.length + 1)) < 1e-10);
      }
    }
  }
});

test('returned decorative positions are independently frozen without shared mutable records', () => {
  const first = chairPositions(30);
  const second = chairPositions(30);
  assert.deepEqual(first, second);
  assert.notStrictEqual(first[0], second[0]);
  assert.ok(first.every(Object.isFrozen));
  assert.throws(() => { first[0].offset = 999; }, TypeError);
  assert.equal(second[0].offset, 100 / 9);
});

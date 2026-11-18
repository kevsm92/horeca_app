import test from 'node:test';
import assert from 'node:assert/strict';
import { chairPositions } from '../src/chairPositions.js';

// Decorative furniture geometry only; Python remains authoritative for physical capacity.
test('all supported capacities render one unique position per chair', () => {
  for (let capacity = 1; capacity <= 30; capacity++) {
    const chairs = chairPositions(capacity);
    assert.equal(chairs.length, capacity, `capacity ${capacity}`);
    assert.equal(new Set(chairs.map(({ side, offset }) => `${side}:${offset}`)).size, capacity);
    assert.ok(chairs.every(({ offset }) => Number.isFinite(offset) && offset > 0 && offset < 100));
  }
});

test('chairs are distributed evenly across sides for every supported capacity', () => {
  for (let capacity = 1; capacity <= 30; capacity++) {
    const counts = Object.values(Object.groupBy(chairPositions(capacity), chair => chair.side)).map(group => group.length);
    assert.ok(Math.max(...counts) - Math.min(...counts) <= 1, `capacity ${capacity}`);
  }
});

test('each side has monotonically increasing chair offsets', () => {
  for (let capacity = 1; capacity <= 30; capacity++) {
    for (const side of ['top', 'right', 'bottom', 'left']) {
      const offsets = chairPositions(capacity).filter(chair => chair.side === side).map(chair => chair.offset);
      assert.deepEqual(offsets, [...offsets].sort((a, b) => a - b), `${capacity} seats, ${side}`);
    }
  }
});

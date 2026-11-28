import test from 'node:test';
import assert from 'node:assert/strict';
import { chairPositions } from '../src/chairPositions.js';

// Decorative geometry only: this must never be used as operational seating validation.
test('rejects invalid decorative capacities without coercion or allocation', () => {
  for (const invalid of [undefined, null, false, true, '', '4', 0, -1, 31, 1.5, NaN, Infinity, -Infinity, {}, [], 4n]) {
    assert.deepEqual(chairPositions(invalid), [], `invalid capacity ${String(invalid)}`);
  }
});

test('boundary capacities generate only finite percentages strictly within each table edge', () => {
  for (const capacity of [1, 2, 3, 4, 29, 30]) {
    const chairs = chairPositions(capacity);
    assert.equal(chairs.length, capacity);
    for (const chair of chairs) {
      assert.ok(['top', 'right', 'bottom', 'left'].includes(chair.side));
      assert.ok(Number.isFinite(chair.offset) && chair.offset > 0 && chair.offset < 100);
    }
  }
});

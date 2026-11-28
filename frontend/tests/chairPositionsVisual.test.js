import test from 'node:test';
import assert from 'node:assert/strict';
import {chairPositions} from '../src/chairPositions.js';

// Decorative, synthetic floor-plan chairs; Python owns physical seat capacity.
test('each supported capacity renders exactly one chair per visual seat', () => {
  for (let capacity = 1; capacity <= 30; capacity++) {
    const chairs = chairPositions(capacity);
    assert.equal(chairs.length, capacity);
    assert.ok(chairs.every(chair => ['top', 'right', 'bottom', 'left'].includes(chair.side)));
    assert.ok(chairs.every(chair => Number.isFinite(chair.offset) && chair.offset > 0 && chair.offset < 100));
  }
});

test('chairs on each edge have unique, evenly spaced offsets', () => {
  for (let capacity = 1; capacity <= 30; capacity++) {
    const chairs = chairPositions(capacity);
    for (const side of ['top', 'right', 'bottom', 'left']) {
      const offsets = chairs.filter(chair => chair.side === side).map(chair => chair.offset);
      assert.equal(new Set(offsets).size, offsets.length);
      offsets.forEach((offset, i) => assert.ok(Math.abs(offset - (i + 1) * 100 / (offsets.length + 1)) < 1e-9));
    }
  }
});

test('invalid capacities cannot allocate decorative chairs', () => {
  for (const capacity of [0, -1, 31, 2.5, NaN, Infinity, '4', null, undefined]) {
    assert.deepEqual(chairPositions(capacity), []);
  }
});

test('rendering chairs does not mutate the returned seat descriptions', () => {
  const chairs = chairPositions(6);
  assert.ok(chairs.every(Object.isFrozen));
  assert.deepEqual(chairs.map(chair => chair.side), ['top', 'right', 'bottom', 'left', 'top', 'right']);
});

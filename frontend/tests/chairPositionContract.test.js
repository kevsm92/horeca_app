import test from 'node:test';
import assert from 'node:assert/strict';
import { chairPositions } from '../src/chairPositions.js';

// Decorative geometry only; Python owns physical seats and seating decisions.
test('every supported capacity produces bounded, evenly distributed decorative chairs', () => {
  const sides = ['top', 'right', 'bottom', 'left'];
  for (let capacity = 1; capacity <= 30; capacity++) {
    const chairs = chairPositions(capacity);
    assert.equal(chairs.length, capacity);
    assert.ok(Object.isFrozen(chairs[0]));
    for (const [index, chair] of chairs.entries()) {
      assert.equal(chair.side, sides[index % 4]);
      assert.ok(Number.isFinite(chair.offset) && chair.offset > 0 && chair.offset < 100);
    }
    const counts = sides.map(side => chairs.filter(chair => chair.side === side).length);
    assert.ok(Math.max(...counts) - Math.min(...counts) <= 1);
    for (const side of sides) {
      const offsets = chairs.filter(chair => chair.side === side).map(chair => chair.offset);
      for (let i = 1; i < offsets.length; i++) {
        assert.ok(offsets[i] > offsets[i - 1], `non-increasing offsets for ${capacity} chairs on ${side}`);
      }
    }
  }
});

test('invalid capacities never create decorative chairs', () => {
  for (const capacity of [undefined, null, NaN, Infinity, -Infinity, -1, 0, 1.5, 30.5, 31, '4', {}, []]) {
    assert.deepEqual(chairPositions(capacity), []);
  }
});

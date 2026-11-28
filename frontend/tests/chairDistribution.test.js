import test from 'node:test';
import assert from 'node:assert/strict';
import { chairPositions } from '../src/chairPositions.js';

// Purely decorative UI geometry; Python remains authoritative for physical seats.
test('decorative chair layout balances all supported capacities across four sides', () => {
  const sides = ['top', 'right', 'bottom', 'left'];
  for (let capacity = 1; capacity <= 30; capacity++) {
    const chairs = chairPositions(capacity);
    assert.equal(chairs.length, capacity);
    const counts = sides.map(side => chairs.filter(chair => chair.side === side).length);
    assert.ok(Math.max(...counts) - Math.min(...counts) <= 1, `unbalanced capacity ${capacity}`);
    for (const side of sides) {
      const offsets = chairs.filter(chair => chair.side === side).map(chair => chair.offset);
      assert.equal(new Set(offsets).size, offsets.length, `duplicate ${side} offset at ${capacity}`);
      assert.ok(offsets.every((offset, i) => offset > 0 && offset < 100 && (i === 0 || offset > offsets[i - 1])));
      for (let i = 0; i < offsets.length; i++) {
        assert.ok(Math.abs(offsets[i] - (i + 1) * 100 / (offsets.length + 1)) < 1e-9);
      }
    }
  }
});

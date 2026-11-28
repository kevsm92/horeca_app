import test from 'node:test';
import assert from 'node:assert/strict';
import { chairPositions } from '../src/chairPositions.js';

// Synthetic decorative geometry only; no seating or capacity authority in React.
test('opposite chair offsets remain mirror-symmetric for every supported capacity', () => {
  for (let seats = 1; seats <= 30; seats++) {
    const chairs = chairPositions(seats);
    for (const side of ['top', 'right', 'bottom', 'left']) {
      const offsets = chairs.filter(chair => chair.side === side).map(chair => chair.offset);
      for (let i = 0; i < offsets.length; i++) {
        assert.ok(Math.abs(offsets[i] + offsets[offsets.length - i - 1] - 100) < 1e-9,
          `asymmetric chair offsets for ${seats} seats on ${side}`);
      }
    }
  }
});

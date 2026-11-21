import test from 'node:test';
import assert from 'node:assert/strict';
import { moveTable } from '../src/floorLayout.js';

// Synthetic visual spacing only; Python owns real table capacity and seating.
test('demo floor rejects overlap strictly inside the 12-unit visual gap', () => {
  const positions = Object.freeze({ T1: Object.freeze({ x: 20, y: 20 }), T2: Object.freeze({ x: 50, y: 50 }) });
  for (const [x, y] of [[38.001, 50], [50, 38.001], [61.999, 50], [50, 61.999], [38.001, 38.001]]) {
    assert.equal(moveTable(positions, 'T1', x, y), positions, `(${x}, ${y}) should be rejected`);
  }
  assert.deepEqual(positions.T1, { x: 20, y: 20 });
});

test('demo floor permits touching the visual gap threshold and orthogonal separation', () => {
  const positions = Object.freeze({ T1: Object.freeze({ x: 20, y: 20 }), T2: Object.freeze({ x: 50, y: 50 }) });
  for (const [x, y] of [[38, 50], [50, 38], [62, 50], [50, 62], [38, 38], [37, 50]]) {
    const next = moveTable(positions, 'T1', x, y);
    assert.notEqual(next, positions, `(${x}, ${y}) should be allowed`);
    assert.deepEqual(next.T1, { x, y });
    assert.equal(next.T2, positions.T2);
  }
});

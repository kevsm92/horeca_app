import test from 'node:test';
import assert from 'node:assert/strict';
import {chairPositions} from '../src/chairPositions.js';
test('one decorative chair per physical seat', () => {
  for (const seats of [1,2,4,6,8,12,30]) {
    const chairs=chairPositions(seats);
    assert.equal(chairs.length,seats);
    assert.ok(chairs.every(c=>['top','right','bottom','left'].includes(c.side)&&c.offset>0&&c.offset<100));
  }
});
test('invalid capacities produce no furniture', () => {
  for (const value of [0,-1,2.5,31,NaN,'4',null]) assert.deepEqual(chairPositions(value),[]);
});
test('positions are deterministic and immutable', () => {
  assert.deepEqual(chairPositions(6),chairPositions(6));
  assert.ok(Object.isFrozen(chairPositions(6)[0]));
});

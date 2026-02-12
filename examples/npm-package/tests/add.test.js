import test from 'node:test';
import assert from 'node:assert/strict';
import { add } from '../index.js';

test('adds numbers', () => {
  assert.equal(add(2, 2), 4);
});

test('handles zero and negatives', () => {
  assert.equal(add(0, 0), 0);
  assert.equal(add(-2, 5), 3);
  assert.equal(add(-3, -7), -10);
});

test('is commutative', () => {
  assert.equal(add(9, -4), add(-4, 9));
});

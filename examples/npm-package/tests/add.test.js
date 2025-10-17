import test from 'node:test';
import assert from 'node:assert/strict';
import { add } from '../index.js';

test('adds numbers', () => {
  assert.equal(add(2, 2), 4);
});

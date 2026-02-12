import test from 'node:test';
import assert from 'node:assert/strict';
import { greet } from '../lib.js';

test('greets name', () => {
  assert.equal(greet('world'), 'hello world');
});

test('handles empty name', () => {
  assert.equal(greet(''), 'hello ');
});

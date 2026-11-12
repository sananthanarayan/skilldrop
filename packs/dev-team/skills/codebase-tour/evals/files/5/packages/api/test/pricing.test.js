import { test } from 'node:test';
import assert from 'node:assert/strict';
import { quote } from '../src/services/pricing.js';

test('charges the nightly rate for short stays', () => {
  assert.equal(quote({ nights: 3 }), 360);
});

test('adds a fee per extra guest per night', () => {
  assert.equal(quote({ nights: 2, guests: 4 }), 300);
});

test('applies the weekly discount from 7 nights', () => {
  assert.equal(quote({ nights: 7 }), 756);
});

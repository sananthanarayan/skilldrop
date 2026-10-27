import { test } from 'node:test';
import assert from 'node:assert/strict';
import { formatNights, formatPrice } from '../src/format.js';

test('formats prices in euros with two decimals', () => {
  assert.equal(formatPrice(756), '€756.00');
});

test('pluralises nights', () => {
  assert.equal(formatNights(1), '1 night');
  assert.equal(formatNights(14), '14 nights');
});

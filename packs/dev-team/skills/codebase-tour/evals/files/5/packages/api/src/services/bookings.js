import { db } from '../db.js';
import { isEnabled } from '../flags.js';
import { quote } from './pricing.js';

// Business rule: no stay may be longer than two weeks.
const MAX_NIGHTS = 14;
const LONG_STAY_MAX_NIGHTS = 28;

export function maxNightsFor(member) {
  if (member && isEnabled('long-stays')) return LONG_STAY_MAX_NIGHTS;
  return MAX_NIGHTS;
}

export async function createBooking({ cabinId, checkIn, nights, guests = 1 }, member) {
  const max = maxNightsFor(member);
  if (nights > max) {
    const err = new Error(`Stays are limited to ${max} nights`);
    err.status = 422;
    throw err;
  }
  const price = quote({ nights, guests });
  return db.insertBooking({ cabinId, checkIn, nights, guests, price, memberId: member?.id ?? null });
}

// Client-side checks for the booking form, run before POST /bookings.
export const MAX_NIGHTS = 14;
export const MAX_GUESTS = 8;

export function validateBookingForm({ nights, guests }) {
  const errors = {};
  if (!Number.isInteger(nights) || nights < 1) errors.nights = 'Choose at least one night';
  else if (nights > MAX_NIGHTS) errors.nights = `Stays are limited to ${MAX_NIGHTS} nights`;
  if (!Number.isInteger(guests) || guests < 1 || guests > MAX_GUESTS) errors.guests = `1 to ${MAX_GUESTS} guests`;
  return errors;
}

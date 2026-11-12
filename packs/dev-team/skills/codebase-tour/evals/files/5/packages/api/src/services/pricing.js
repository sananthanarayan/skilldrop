const NIGHTLY_RATE = 120;
const EXTRA_GUEST_FEE = 15;
const WEEKLY_DISCOUNT = 0.1;

export function quote({ nights, guests = 1 }) {
  const base = nights * NIGHTLY_RATE + Math.max(0, guests - 2) * EXTRA_GUEST_FEE * nights;
  const discount = nights >= 7 ? base * WEEKLY_DISCOUNT : 0;
  return Math.round((base - discount) * 100) / 100;
}

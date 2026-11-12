export function formatPrice(amount) {
  return `€${amount.toFixed(2)}`;
}

export function formatNights(n) {
  return n === 1 ? '1 night' : `${n} nights`;
}

// RFC-0003: money is integer minor units.
export function assertMinorUnits(amountMinor: number): void {
  if (!Number.isInteger(amountMinor) || amountMinor < 0) {
    throw new Error("amountMinor must be a non-negative integer");
  }
}

export function formatAmount(amountMinor: number, currency: string, digits = 2): string {
  return `${(amountMinor / 10 ** digits).toFixed(digits)} ${currency}`;
}

export interface Invoice {
  id: string;
  tenantId: string;
  dueDate: string; // ISO date, e.g. "2026-03-01"
  balance: number; // dollars outstanding
  status: "open" | "paid" | "void";
}

const GRACE_DAYS = 5;
const MONTHLY_RATE = 0.015;
const FEE_CAP = 75;
const MS_PER_DAY = 86_400_000;

function parseDue(inv: Invoice): Date {
  return new Date(inv.dueDate + "T00:00:00Z");
}

export function daysLate(inv: Invoice, today: Date): number {
  return Math.floor((today.getTime() - parseDue(inv).getTime()) / MS_PER_DAY);
}

// Number of calendar months the invoice has been overdue in, counting the
// month it fell due. Due 20 March, today 2 May -> 3.
export function monthsOverdue(inv: Invoice, today: Date): number {
  return today.getUTCMonth() - parseDue(inv).getUTCMonth() + 1;
}

export function computeLateFee(inv: Invoice, today: Date): number {
  if (inv.status !== "open") return 0;
  if (daysLate(inv, today) <= GRACE_DAYS) return 0;

  const monthly = Math.min(inv.balance * MONTHLY_RATE, FEE_CAP);
  const fee = monthly * monthsOverdue(inv, today);
  return Math.round(fee * 100) / 100;
}

// Called by the nightly job with every invoice for the portfolio.
export function applyLateFees(invoices: Invoice[], today: Date): Invoice[] {
  for (const inv of invoices) {
    const fee = computeLateFee(inv, today);
    if (fee > 0) {
      inv.balance += fee;
    }
  }
  return invoices;
}

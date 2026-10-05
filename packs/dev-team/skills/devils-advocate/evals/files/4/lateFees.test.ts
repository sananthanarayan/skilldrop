import { describe, it, expect } from "vitest";
import { applyLateFees, computeLateFee, Invoice } from "./lateFees";

const day = (s: string) => new Date(s + "T12:00:00Z");

const invoice = (over: Partial<Invoice> = {}): Invoice => ({
  id: "INV-1001",
  tenantId: "T-204",
  dueDate: "2026-03-01",
  balance: 1000,
  status: "open",
  ...over,
});

describe("computeLateFee", () => {
  it("charges nothing inside the grace period", () => {
    expect(computeLateFee(invoice(), day("2026-03-06"))).toBe(0);
  });

  it("charges 1.5% once the grace period is over", () => {
    expect(computeLateFee(invoice(), day("2026-03-07"))).toBe(15);
  });

  it("charges for each calendar month overdue", () => {
    const inv = invoice({ dueDate: "2026-03-20" });
    expect(computeLateFee(inv, day("2026-05-02"))).toBe(45);
  });

  it("caps the fee at $75", () => {
    const inv = invoice({ balance: 10000 });
    expect(computeLateFee(inv, day("2026-03-10"))).toBe(75);
  });

  it("never charges paid or void invoices", () => {
    expect(computeLateFee(invoice({ status: "paid" }), day("2026-06-01"))).toBe(0);
    expect(computeLateFee(invoice({ status: "void" }), day("2026-06-01"))).toBe(0);
  });
});

describe("applyLateFees", () => {
  it("adds the fee to open invoices", () => {
    const inv = invoice();
    applyLateFees([inv], day("2026-03-10"));
    expect(inv.balance).toBeGreaterThan(1000);
  });
});

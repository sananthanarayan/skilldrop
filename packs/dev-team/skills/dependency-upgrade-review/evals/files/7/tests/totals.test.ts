import { describe, it, expect } from "vellum-test";
import { lineTotal, invoiceTotal } from "../src/totals";

describe("totals", () => {
  it("multiplies quantity by unit price in minor units", () => {
    expect(lineTotal({ qty: 3, unitMinor: 1250 })).toBe(3750);
  });

  it("sums lines", () => {
    expect(invoiceTotal([{ qty: 1, unitMinor: 100 }, { qty: 2, unitMinor: 50 }])).toBe(200);
  });
});

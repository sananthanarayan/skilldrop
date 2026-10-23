import type { DeepReadonly } from "tsforge-types";

export type Line = DeepReadonly<{ qty: number; unitMinor: number }>;

export function lineTotal(l: Line): number {
  return l.qty * l.unitMinor;
}

export function invoiceTotal(lines: readonly Line[]): number {
  return lines.reduce((sum, l) => sum + lineTotal(l), 0);
}

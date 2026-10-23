import type { Brand } from "tsforge-types";

export type IsoDate = Brand<string, "IsoDate">;

const DAY_MS = 24 * 60 * 60 * 1000;

export function isOverdue(inv: { dueAt: string }): boolean {
  return Date.now() > Date.parse(inv.dueAt);
}

export function formatDue(inv: { dueAt: string }): string {
  const days = Math.round((Date.parse(inv.dueAt) - Date.now()) / DAY_MS);
  if (days < 0) return `overdue by ${-days} days`;
  if (days === 0) return "due today";
  return `due in ${days} days`;
}

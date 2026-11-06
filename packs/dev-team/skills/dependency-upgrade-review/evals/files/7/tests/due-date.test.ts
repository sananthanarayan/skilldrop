import { describe, it, expect, vt } from "vellum-test";
import { isOverdue, formatDue } from "../src/due-date";

describe("due dates", () => {
  it("flags invoices past their due date", () => {
    vt.fakeTimers({ now: new Date("2026-03-15T09:00:00Z") });
    expect(isOverdue({ dueAt: "2026-03-14T23:59:59Z" })).toBe(true);
    expect(isOverdue({ dueAt: "2026-03-16T00:00:00Z" })).toBe(false);
    vt.restoreTimers();
  });

  it("formats relative due text", () => {
    vt.fakeTimers({ now: new Date("2026-03-15T09:00:00Z") });
    expect(formatDue({ dueAt: "2026-03-18T09:00:00Z" })).toBe("due in 3 days");
    vt.restoreTimers();
  });
});

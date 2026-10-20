import { describe, it, expect } from "vitest";
import { parseListQuery } from "../../src/http/handlers/shipments.js";

const config = { port: 0, databaseUrl: "postgres://unused", maxPageSize: 100, legacySort: false };

describe("parseListQuery", () => {
  it("accepts a known status", () => {
    expect(parseListQuery({ status: "delivered" }, config)).toEqual({ status: "delivered" });
  });

  it("rejects an unknown status with invalid_status", () => {
    expect(() => parseListQuery({ status: "lost" }, config)).toThrowError(/status must be one of/);
  });

  it("rejects a limit above maxPageSize", () => {
    expect(() => parseListQuery({ limit: "500" }, config)).toThrowError(/limit must be/);
  });
});

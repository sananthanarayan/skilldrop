import { describe, it, expect } from "vitest";
import { buildShipmentFilter } from "../../src/domain/shipments/filter.js";

const config = { port: 0, databaseUrl: "postgres://unused", maxPageSize: 100, legacySort: false };

describe("buildShipmentFilter", () => {
  it("adds a status clause with a positional parameter", () => {
    const f = buildShipmentFilter({ status: "pending" }, config);
    expect(f.where).toEqual(["status = $1"]);
    expect(f.params).toEqual(["pending"]);
  });

  it("sorts ascending when legacySort is on", () => {
    expect(buildShipmentFilter({}, { ...config, legacySort: true }).orderBy).toBe("created_at ASC");
  });
});

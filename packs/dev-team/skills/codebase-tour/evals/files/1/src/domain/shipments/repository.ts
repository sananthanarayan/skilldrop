import pg from "pg";
import type { Config } from "../../config.js";
import type { ShipmentFilter } from "./filter.js";

export async function queryShipments(config: Config, filter: ShipmentFilter) {
  const client = new pg.Client({ connectionString: config.databaseUrl });
  await client.connect();
  try {
    const where = filter.where.length ? "WHERE " + filter.where.join(" AND ") : "";
    const sql = `SELECT id, status, carrier, created_at FROM shipments ${where} ORDER BY ${filter.orderBy} LIMIT ${filter.limit}`;
    return (await client.query(sql, filter.params)).rows;
  } finally {
    await client.end();
  }
}

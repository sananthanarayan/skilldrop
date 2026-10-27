// Nightly CSV export for the finance team. Runs from the scheduler, not the API.
import pg from "pg";
import { loadConfig } from "../config.js";

export async function exportShipments(status?: string): Promise<string> {
  const config = loadConfig();
  const client = new pg.Client({ connectionString: config.databaseUrl });
  await client.connect();
  try {
    // Same filtering as the list endpoint, kept here so the job has no HTTP dependency.
    const params: unknown[] = [];
    let where = "";
    if (status) {
      params.push(status);
      where = "WHERE status = $1";
    }
    const rows = (await client.query(`SELECT id, status, carrier FROM shipments ${where} ORDER BY created_at DESC`, params)).rows;
    return rows.map((r) => [r.id, r.status, r.carrier].join(",")).join("\n");
  } finally {
    await client.end();
  }
}

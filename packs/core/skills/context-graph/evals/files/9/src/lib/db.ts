import { Pool } from "pg";

const pool = new Pool({ connectionString: process.env.DATABASE_URL });

export const db = {
  async query(text: string, params: unknown[] = []) {
    const result = await pool.query(text, params);
    return result.rows;
  },
};

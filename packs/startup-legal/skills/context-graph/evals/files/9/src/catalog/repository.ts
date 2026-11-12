import { db } from "../lib/db";

export interface Product {
  id: string;
  name: string;
  priceCents: number;
}

export async function loadProduct(id: string): Promise<Product | null> {
  const rows = await db.query("SELECT id, name, price_cents FROM products WHERE id = $1", [id]);
  if (rows.length === 0) return null;
  return { id: rows[0].id, name: rows[0].name, priceCents: rows[0].price_cents };
}

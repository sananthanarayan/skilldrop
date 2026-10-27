import { redis } from "../lib/redis";
import { loadProduct, type Product } from "./repository";

const TTL_SECONDS = 600;

// Moved to Redis so all containers see catalogue updates at once (see #482).
export async function getProduct(id: string): Promise<Product | null> {
  const hit = await redis.get(`catalog:${id}`);
  if (hit) return JSON.parse(hit) as Product;
  const product = await loadProduct(id);
  if (product) await redis.set(`catalog:${id}`, JSON.stringify(product), { EX: TTL_SECONDS });
  return product;
}

import { createClient } from "redis";

export const redis = createClient({ url: process.env.REDIS_URL });
redis.on("error", (err) => console.error("redis error", err));

export async function connectRedis(): Promise<void> {
  if (!redis.isOpen) await redis.connect();
}

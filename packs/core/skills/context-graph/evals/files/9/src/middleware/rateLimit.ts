import type { Request, Response, NextFunction } from "express";
import { redis } from "../lib/redis";

const LIMIT_PER_MINUTE = 600;

const TAKE_TOKEN = `
local tokens = tonumber(redis.call('GET', KEYS[1]) or ARGV[1])
if tokens <= 0 then return 0 end
redis.call('SET', KEYS[1], tokens - 1, 'EX', 60, 'KEEPTTL')
return 1
`;

export async function rateLimit(req: Request, res: Response, next: NextFunction) {
  const apiKey = req.header("x-api-key");
  if (!apiKey) return next();
  try {
    const ok = await redis.eval(TAKE_TOKEN, {
      keys: [`rl:${apiKey}`],
      arguments: [String(LIMIT_PER_MINUTE)],
    });
    if (ok === 0) return res.status(429).json({ error: "rate_limited" });
  } catch {
    // fail open, per decision 002
  }
  next();
}

import session from "express-session";
import RedisStore from "connect-redis";
import { redis } from "../lib/redis";

export const sessionMiddleware = session({
  store: new RedisStore({ client: redis, prefix: "sess:", ttl: 60 * 60 * 24 * 7 }),
  secret: process.env.SESSION_SECRET ?? "",
  resave: false,
  saveUninitialized: false,
});

import express from "express";
import { connectRedis } from "./lib/redis";
import { sessionMiddleware } from "./session/store";
import { rateLimit } from "./middleware/rateLimit";
import { getProduct } from "./catalog/cache";

const app = express();
app.use(sessionMiddleware);
app.use("/v1", rateLimit);

app.get("/v1/products/:id", async (req, res) => {
  const product = await getProduct(req.params.id);
  if (!product) return res.status(404).end();
  res.json(product);
});

connectRedis().then(() => app.listen(3000));

import express from "express";
import { loadConfig } from "./config.js";
import { registerRoutes } from "./http/routes.js";
import { HttpError } from "./errors.js";

const config = loadConfig();
const app = express();
registerRoutes(app, config);

app.use((err: unknown, _req: express.Request, res: express.Response, _next: express.NextFunction) => {
  if (err instanceof HttpError) {
    res.status(err.status).json({ error: err.code, message: err.message });
    return;
  }
  res.status(500).json({ error: "internal" });
});

app.listen(config.port);

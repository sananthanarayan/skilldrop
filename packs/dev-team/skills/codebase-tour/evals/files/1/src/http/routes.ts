import type { Express } from "express";
import type { Config } from "../config.js";
import { listShipments } from "./handlers/shipments.js";

export function registerRoutes(app: Express, config: Config): void {
  app.get("/shipments", listShipments(config));
}

import type { Request, Response, NextFunction } from "express";
import type { Config } from "../../config.js";
import type { ListShipmentsQuery } from "../../generated/api-types.js";
import { badRequest } from "../../errors.js";
import { buildShipmentFilter } from "../../domain/shipments/filter.js";
import { queryShipments } from "../../domain/shipments/repository.js";

const STATUSES = ["pending", "in_transit", "delivered"];

export function parseListQuery(raw: Record<string, unknown>, config: Config): ListShipmentsQuery {
  const query: ListShipmentsQuery = {};
  if (raw.status !== undefined) {
    if (typeof raw.status !== "string" || !STATUSES.includes(raw.status)) {
      throw badRequest("invalid_status", "status must be one of " + STATUSES.join(", "));
    }
    query.status = raw.status as ListShipmentsQuery["status"];
  }
  if (raw.limit !== undefined) {
    const limit = Number(raw.limit);
    if (!Number.isInteger(limit) || limit < 1 || limit > config.maxPageSize) {
      throw badRequest("invalid_limit", "limit must be 1.." + config.maxPageSize);
    }
    query.limit = limit;
  }
  return query;
}

export function listShipments(config: Config) {
  return async (req: Request, res: Response, next: NextFunction) => {
    try {
      const query = parseListQuery(req.query, config);
      const filter = buildShipmentFilter(query, config);
      res.json({ items: await queryShipments(config, filter) });
    } catch (err) {
      next(err);
    }
  };
}

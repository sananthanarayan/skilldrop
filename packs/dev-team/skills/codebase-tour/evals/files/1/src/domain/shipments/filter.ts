import type { Config } from "../../config.js";
import type { ListShipmentsQuery } from "../../generated/api-types.js";

export interface ShipmentFilter {
  where: string[];
  params: unknown[];
  orderBy: string;
  limit: number;
}

export function buildShipmentFilter(query: ListShipmentsQuery, config: Config): ShipmentFilter {
  const where: string[] = [];
  const params: unknown[] = [];
  if (query.status) {
    params.push(query.status);
    where.push(`status = $${params.length}`);
  }
  return {
    where,
    params,
    orderBy: config.legacySort ? "created_at ASC" : "created_at DESC",
    limit: query.limit ?? 50,
  };
}

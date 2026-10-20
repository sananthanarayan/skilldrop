export interface Config {
  port: number;
  databaseUrl: string;
  maxPageSize: number;
  legacySort: boolean;
}

export function loadConfig(): Config {
  const databaseUrl = process.env.DATABASE_URL;
  if (!databaseUrl) {
    throw new Error("DATABASE_URL is required");
  }
  return {
    port: Number(process.env.PORT ?? 3000),
    databaseUrl,
    maxPageSize: Number(process.env.MAX_PAGE_SIZE ?? 100),
    // Old consoles sort by created_at ascending; remove once v1 console is retired.
    legacySort: process.env.SHIPMENTS_LEGACY_SORT === "1",
  };
}

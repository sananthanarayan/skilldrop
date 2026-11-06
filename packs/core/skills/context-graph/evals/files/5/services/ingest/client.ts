import { withRetry } from "./retry";
import type { FeedEvent } from "../../lib/types";

const FEED_URL = process.env.PARTNER_FEED_URL ?? "https://feed.partner.example/v2/events";

export async function fetchEvents(cursor: string): Promise<FeedEvent[]> {
  return withRetry(async () => {
    const res = await fetch(`${FEED_URL}?cursor=${encodeURIComponent(cursor)}`, {
      signal: AbortSignal.timeout(10_000),
    });
    if (!res.ok) throw new Error(`feed ${res.status}`);
    return (await res.json()) as FeedEvent[];
  });
}

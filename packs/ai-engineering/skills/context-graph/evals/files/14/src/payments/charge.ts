import { retryProcessorCall } from "./retry";
import { assertMinorUnits } from "./amount";
import { idempotencyStore } from "./idempotency";
import { sendWebhook } from "../webhooks/send";

export interface ChargeRequest {
  amountMinor: number; // integer minor units, see RFC-0003
  currency: string;    // ISO 4217
  cardToken: string;
}

export async function createCharge(req: ChargeRequest, headers: Record<string, string>) {
  const key = headers["idempotency-key"];
  if (!key) {
    return { status: 400, body: { error: "Idempotency-Key header is required" } }; // RFC-0001
  }
  const previous = await idempotencyStore.get(key);
  if (previous) return previous;

  assertMinorUnits(req.amountMinor);
  const result = await retryProcessorCall(() => processor.charge(req));
  const response = { status: 201, body: result };
  await idempotencyStore.put(key, response, 24 * 3600);
  await sendWebhook("charge.succeeded", result);
  return response;
}

declare const processor: { charge(req: ChargeRequest): Promise<unknown> };

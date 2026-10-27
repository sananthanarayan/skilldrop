import { retryIfSafe } from "./retry";
import type { Invoice } from "../../lib/types";

const BILLING_URL = process.env.PARTNER_BILLING_URL ?? "https://billing.partner.example/v1/invoices";

export async function pushInvoice(inv: Invoice, idempotencyKey: string): Promise<Response> {
  return retryIfSafe(() =>
    fetch(BILLING_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json", "Idempotency-Key": idempotencyKey },
      body: JSON.stringify(inv),
      signal: AbortSignal.timeout(15_000),
    }),
  );
}

import { createHmac } from "crypto";

// RFC-0004: the single place outbound webhooks are signed.
export function signPayload(secret: string, timestamp: number, body: string): string {
  return createHmac("sha256", secret).update(`${timestamp}.${body}`).digest("hex");
}

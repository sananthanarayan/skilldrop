import { signPayload } from "./sign";

export async function sendWebhook(event: string, payload: unknown): Promise<void> {
  const body = JSON.stringify({ event, payload });
  const ts = Math.floor(Date.now() / 1000);
  const signature = signPayload(process.env.WEBHOOK_SECRET ?? "placeholder-secret", ts, body);
  console.log("webhook", event, signature.slice(0, 8));
  // HTTP delivery omitted in this excerpt
}

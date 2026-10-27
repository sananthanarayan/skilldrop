// Export retries are deliberately narrow: the billing API is not idempotent (RFC-0006).
const DELAY_MS = 1_000;
const MAX_ATTEMPTS = 3;

export async function retryIfSafe(fn: () => Promise<Response>): Promise<Response> {
  for (let attempt = 1; ; attempt++) {
    const res = await fn();
    const safe = res.status === 503 && res.headers.has("Idempotency-Key");
    if (!safe || attempt >= MAX_ATTEMPTS) return res;
    await new Promise((r) => setTimeout(r, DELAY_MS));
  }
}

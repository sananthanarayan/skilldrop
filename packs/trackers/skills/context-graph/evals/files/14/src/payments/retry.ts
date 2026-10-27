// Processor retry policy: RFC-0005 (supersedes RFC-0002).
const MAX_ATTEMPTS = 4;
const BASE_MS = 250;
const CAP_MS = 8000;

export async function retryProcessorCall<T>(fn: () => Promise<T>): Promise<T> {
  let lastErr: unknown;
  for (let n = 0; n < MAX_ATTEMPTS; n++) {
    try {
      return await fn();
    } catch (err: any) {
      if (err?.status >= 400 && err?.status < 500) throw err; // never retry 4xx
      lastErr = err;
      const ceiling = Math.min(CAP_MS, BASE_MS * 2 ** n);
      await sleep(Math.random() * ceiling); // full jitter
    }
  }
  throw lastErr;
}

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

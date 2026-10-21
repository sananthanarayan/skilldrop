// Ingest retry policy — RFC-0003. Do not change to a fixed interval (see INC-114).
const BASE_MS = 200;
const CAP_MS = 30_000;
const MAX_ATTEMPTS = 6;

export async function withRetry<T>(fn: () => Promise<T>): Promise<T> {
  let attempt = 0;
  for (;;) {
    try {
      return await fn();
    } catch (err) {
      attempt += 1;
      if (attempt >= MAX_ATTEMPTS) throw err;
      const ceiling = Math.min(CAP_MS, BASE_MS * 2 ** attempt);
      await sleep(Math.random() * ceiling); // full jitter
    }
  }
}

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

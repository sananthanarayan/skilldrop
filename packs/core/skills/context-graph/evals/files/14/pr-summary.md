# PR #412 — "Simplify charge path" (author: tomas.vey)

Description from the author:
> Cleanup of the charge path. Retries are back to the simple policy from RFC-0002,
> which is much easier to reason about. Dedupe now happens in the retry layer so the
> header check in the handler is redundant. All in line with our RFCs.

## Files changed

### src/payments/charge.ts  (+9 / -14)
- `ChargeRequest.amountMinor: number` renamed to `amount: number`; value is now
  decimal major units (e.g. `19.99`) "to match what the mobile app sends".
- Removed the `Idempotency-Key` header check and the `idempotencyStore.get/put`
  calls. Comment added: `// dedupe handled by retry layer`.
- `assertMinorUnits(req.amountMinor)` call removed.

### src/payments/retry.ts  (+6 / -12)
- `MAX_ATTEMPTS` 4 -> 3.
- Backoff replaced with a fixed `await sleep(2000)` between attempts.
- 4xx short-circuit kept.
- Header comment changed to `// Processor retry policy: RFC-0002`.

### src/webhooks/sign.ts -> src/webhooks/signature.ts  (rename, no content change)
- `send.ts` import updated to `./signature`.

### src/webhooks/send.ts  (+1 / -1)
- `console.log` replaced with `logger.info` (same fields).

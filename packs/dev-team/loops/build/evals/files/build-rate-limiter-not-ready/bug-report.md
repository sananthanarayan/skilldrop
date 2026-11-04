# BUG-311: Idle tenants can burst far past their plan limit

- Reported: 2026-10-30 by Support (Nadia Haddad), from ticket SUP-9081
- Component: `ratelimit` (API gateway token bucket)
- Severity: S2 (customers can exceed their plan; no data exposure). Priority: P1.

## Symptom

Tenant acct-7781 is on the Starter plan: burst capacity 5, refill 5 tokens per second.
After their integration had been idle overnight, gateway logs show 37 requests from
them accepted within a single second at 07:02:11 UTC on 2026-10-30.

## Repro (verified by Ahmed on a laptop, 2026-10-31)

1. Create `TokenBucket(capacity=5, refill_per_sec=5, clock=fake_clock)`.
2. Advance the fake clock by 3600 seconds without calling `allow()`.
3. Call `allow()` 50 times without advancing the clock.

Expected: 5 calls return True, the rest False.
Actual: 50 calls return True.

## Notes

Refill adds `elapsed * refill_per_sec` with no ceiling, so the bucket grows without
limit while idle.

# Worked example — adversarial review of a just-written rate limiter

Input → output oracle for `devils-advocate`. Shows the four-lens sweep producing
severity-calibrated findings with `file:line` evidence and paste-able fixes — not a
generic "looks good, consider tests" pass.

## Input (the "done" implementation)

> "Implemented the per-user rate limiter, tests pass, ready for review."

```python
# ratelimit.py
_buckets: dict[str, tuple[float, float]] = {}   # user_id -> (tokens, last_refill)

def allow(user_id: str, rate: float, burst: float) -> bool:
    now = time.time()
    tokens, last = _buckets.get(user_id, (burst, now))
    tokens = min(burst, tokens + (now - last) * rate)
    if tokens >= 1:
        _buckets[user_id] = (tokens - 1, now)
        return True
    _buckets[user_id] = (tokens, now)
    return False
```

## Output (the review)

**Verdict: not ready — 1 blocker, 1 major.** Four lenses swept; happy path is fine, the concurrency and growth paths are not.

🟥 **Blocker — race on the shared dict (assumptions lens).** `ratelimit.py:6-11` reads then writes `_buckets[user_id]` with no lock. Two concurrent requests for the same user both read `tokens=1.0`, both pass, both write back `0.0` — the limiter leaks one token per race, so a burst of N parallel requests admits ~2× the intended rate. The "tests pass" because they're single-threaded. *Fix:* guard the read-modify-write with a per-user lock, or move to an atomic backend (Redis `INCR`+TTL). A dict-of-locks keyed by `user_id` is the minimal change.

🟧 **Major — unbounded memory growth (edge-case lens).** `_buckets` never evicts (`:1`). Every distinct `user_id` ever seen stays forever; a service facing the open internet (or spoofable user ids) OOMs over time. *Fix:* cap with an LRU (`functools.lru_cache` won't fit the mutable value — use `cachetools.TTLCache(maxsize=…, ttl=…)`), evicting idle buckets.

🟨 **Minor — first call gets a free full burst (edge-case lens).** A never-seen `user_id` starts at `(burst, now)` (`:6`), so a brand-new user can immediately spend the whole burst. If the intent is "warm up", seed at `min(burst, rate*window)` instead — flag for product, don't silently change.

⚪ **Nit — `rate`/`burst` unvalidated (staff-engineer lens).** `rate<=0` freezes every user out; `burst<1` makes `allow` always false. Assert `rate>0 and burst>=1` at the boundary.

**Test-coverage gaps (the "tests pass" were happy-path only):**
- Concurrency: two threads hammering one `user_id` must not exceed `burst + rate*elapsed` admits.
- Refill: after exhausting tokens, `allow` returns True again only after `1/rate` seconds.
- Eviction: memory stays bounded under 10k distinct ids.
- Boundary: `tokens` sitting at exactly `1.0` admits; at `0.999…` denies.

## Why this passes the quality bar

Severity is calibrated (one blocker, demoted the rest); every finding cites `file:line`, names the *lens* it came from, and gives a concrete fix or a specific missing test — not "add more tests."

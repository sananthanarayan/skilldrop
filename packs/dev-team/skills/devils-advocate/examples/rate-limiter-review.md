# Worked example — review of a rate limiter that "passes its tests"

Input → output oracle for `devils-advocate`. Shows the answer first, findings that survive a
trace through the code, and the cited tests judged for what they could and could not catch.

## Input

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

```python
# test_ratelimit.py
def test_burst_then_deny():
    for _ in range(3):
        assert allow("u1", rate=1, burst=3)
    assert not allow("u1", rate=1, burst=3)
```

## Output (the review)

**Not ready to merge.** Under concurrent requests for one user it admits more than the limit,
and the test can't see that.

1. **Race on the shared dict** — `ratelimit.py:6-10`. Two requests for the same user both read
   `tokens=1.0`, both pass, both write back `0.0`, so parallel bursts get through at up to
   twice the intended rate. Fix: hold a per-user lock around the read-modify-write:

   ```python
   _locks = collections.defaultdict(threading.Lock)

   def allow(user_id, rate, burst):
       with _locks[user_id]:
           ...  # existing body unchanged
   ```

2. **Memory grows without bound** — `ratelimit.py:2`. Nothing ever leaves `_buckets`, so every
   distinct `user_id` stays for the life of the process. Fix: a `cachetools.TTLCache` in place
   of the dict, with a TTL longer than `burst / rate`.

**What the test proves.** `test_burst_then_deny` runs on one thread, so it passes with the
race in place. It also never waits, so refill is untested. Tests that would fail today:

- Ten threads calling `allow("u1", rate=1, burst=3)` at once; assert at most three return
  `True`.
- After draining the bucket, `allow` is false at 0.5 s and true at 1.0 s (with a patched clock).

## Why this passes the quality bar

The merge answer comes first. Each finding names the line, a concrete failure and a fix as
code. The cited test is judged for what it could catch, and the missing tests are scenarios.
The free first burst for a new user was left out: it is a product choice, not a bug in this
change.

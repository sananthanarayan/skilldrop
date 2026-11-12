# Example — council-review on a decision

**Input given to the skill:**

> Should we put a Redis cache in front of our Postgres read queries for the product-catalog API? Catalog reads are ~80% of our traffic and p99 latency has crept to 400ms. Catalog data changes a few times a day via an internal admin tool. Team is 4 engineers, no one currently runs Redis.

This is a **decision** shape (not a diff). Below is the artifact the skill produces.

---

# Council review: Add Redis cache in front of product-catalog reads
_Scope: decision · the question above · Reviewed: 2026-06-05_

## Verdict

**⚠️ PROCEED WITH CONDITIONS**

Cache the catalog reads — the read/write ratio (80% reads, writes a few times a day) is close to the ideal case for caching, and 400ms p99 is a real user-facing problem. But the win is only safe if invalidation is driven by the admin write path, not by a blind TTL, and if the cache is a *performance* dependency the API can lose without going down. We accept running one new piece of infrastructure (Operator's dissent noted) because the latency problem is load-bearing for 80% of traffic and the data shape is genuinely cache-friendly.

**Tradeoff chosen:** one more thing to operate, in exchange for a large latency win on the dominant traffic path.
**What would change our mind:** if catalog write frequency rises to "many times per minute" (e.g. real-time pricing), the invalidation cost flips the math — revisit. Likewise if a profiler shows the 400ms is a missing index, not load — fix that first and the cache may be unnecessary.

### Conditions
1. **Invalidation on write, not just TTL.** The admin tool must bust the affected cache keys on save. Keep a short backstop TTL (e.g. 5 min) for safety, but correctness comes from event-driven invalidation.
2. **Cache is non-critical.** On Redis timeout/miss/down, fall through to Postgres — degraded latency, not an outage. Wrap with a timeout + circuit breaker.
3. **Confirm the cause first.** Run one `EXPLAIN ANALYZE` on the hot query before building. If p99 is a missing index, do that first (cheaper, no new infra).
4. **One metric before, one after.** Capture current p99 and cache hit-rate so the win is measured, not assumed.

## The vote

| Seat | Stance | One-line position |
|---|---|---|
| 🏛 Architect | 🟡 Conditions | Fine if the cache sits behind the repository layer, not sprinkled through handlers. |
| 🔒 Security | ⚪ Abstain | Public catalog data, no PII, no trust boundary crossed. Nothing to add. |
| 🛠 Operator | 🟡 Conditions | I'm now on call for Redis. Acceptable only if the API degrades gracefully without it. |
| ⚖️ Pragmatist | 🟡 Conditions | Probably worth it — but prove it's load, not a missing index, before adding infra. |
| 👤 User-Advocate | 🟡 Conditions | Stale catalog for minutes is mostly fine — except price. Invalidate price-bearing fields on write. |
| ⚡ Performance (bench, seated: latency is the whole point) | 🟢 Support | 80/20 read ratio + small, slow-changing dataset is the textbook cache win. |

_Benched: Cost (single small Redis, negligible), Data & Migration (no schema change), A11y (no UI), Compliance (public data)._

## Cruxes

### Crux 1 — Is the 400ms actually load, or a missing index?
- **Split:** Pragmatist 🟡 / Performance 🟢
- **Turns on:** a missing fact — nobody has profiled the hot query. If it's an unindexed scan, an index fixes p99 with zero new infra; if it's genuine read volume, the cache is right.
- **Resolves with:** one `EXPLAIN ANALYZE` (Condition 3). Cheap to settle before committing.

### Crux 2 — Staleness: acceptable, or a correctness bug?
- **Split:** User-Advocate 🟡 / Performance 🟢 (and Operator's TTL instinct)
- **Turns on:** a tradeoff — a blind TTL is simple but serves stale **prices** for up to the TTL window, which is a real money/trust problem; event-driven invalidation is correct but couples the admin tool to the cache.
- **Resolves with:** invalidate-on-write for price-bearing fields, TTL as backstop only (Condition 1). The Chair takes correctness over simplicity here because wrong prices are not a "minor staleness" issue.

## Positions (detail)

### 🏛 Architect — 🟡 Conditions
- Put the cache read/write inside the existing `CatalogRepository`, not in the API handlers. One seam, one place to reason about invalidation. Sprinkling `redis.get` through handlers (the tempting quick version) couples every endpoint to the cache and makes invalidation un-auditable.

### 🔒 Security — ⚪ Abstain
- Catalog is public, read-only, no PII. No new trust boundary. (Stated rather than inventing a concern.)

### 🛠 Operator — 🟡 Conditions
- A new stateful dependency means a new pager rotation, a new thing that can OOM or fail over. Acceptable **only** if a Redis outage degrades the API to "slower," not "down" — timeout + circuit breaker + fall-through to Postgres (Condition 2). Add a hit-rate + Redis-availability metric.

### ⚖️ Pragmatist — 🟡 Conditions
- Don't add infra to fix a problem we haven't diagnosed. Profile first (Condition 3). If it's load, the cache is justified and I support it — this isn't gold-plating, it's the right tool for an 80%-read path. Just earn it with one query plan.

### 👤 User-Advocate — 🟡 Conditions
- Users tolerate a slightly stale *description* or *image*. They do **not** tolerate a stale **price** at checkout. Invalidation must cover price-bearing fields immediately on admin save; everything else can ride the TTL.

### ⚡ Performance — 🟢 Support
- 80% reads, dataset small enough to fit in memory, changes a few times a day: this is the canonical caching win. Expect p99 to drop from ~400ms to single-digit-ms on cache hits. The win scales with the read ratio, which is already dominant.

## Dissent on record
**Operator** supported only under conditions and wants it on record that this adds permanent operational surface for a 4-person team with no current Redis experience. Watch: if Redis-related pages exceed ~1/month or the team can't keep hit-rate healthy, the operational cost may outweigh the latency win — that's the trigger to reconsider (ties to "what would change our mind"). The graceful-degradation requirement (Condition 2) exists specifically so that a Redis incident is a latency blip, not a catalog outage.

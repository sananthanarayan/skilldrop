# Lens 2: Future-proofing — assumptions that won't survive 6 months

The question this lens asks: **what assumptions are baked into this code that will hurt when something predictable changes?**

This is not "design for every hypothetical." It's "the obvious next requirements will break this." Flag only assumptions whose violation is *likely* within a year — not theoretical.

---

## Scale assumptions

- **Hard-coded limits.** `LIMIT 100`, `for (i = 0; i < 1000; i++)`, `maxResults = 50`. What happens at 2× current scale? 10×?
- **In-memory accumulation.** Loading the whole result set into a list, holding it, then processing. Will it OOM at next year's data volume?
- **Unbounded growth.** A list / map / queue with no eviction. Will memory grow forever?
- **N+1 queries.** Loop calls the DB per iteration. Fine at 10 items, dead at 10,000.
- **Synchronous calls in a hot path.** Add three more downstream services and the latency stacks.

## Tenancy assumptions

- **Single-tenant baked in.** No `tenant_id` / `org_id` / `workspace_id` threaded through. Will be a multi-week refactor when multi-tenancy lands.
- **Global state.** Caches keyed only by user/id, no tenant scope.
- **Per-user limits where per-tenant is needed** (or vice versa).
- **Email / username uniqueness assumed globally** rather than per-tenant.

## Identity / ownership assumptions

- **Hard-coded user / account / org IDs.** `if (orgId === 'acme-corp')`. Will rot the moment Acme renames.
- **"Admin" as a single role** when next year wants RBAC with custom roles.
- **API keys with no rotation path.** What's the story when one leaks?
- **Auth provider baked into business logic.** Migrating providers means rewriting business code.

## Data / schema assumptions

- **Enum hard-coded in code** when next year wants user-configurable values.
- **Boolean flag** that becomes a tri-state (`yes / no / pending`) or n-state.
- **JSONB blob** with no versioning — when its shape evolves, old rows can't be read or written without compat shims.
- **Foreign key to a "single source of truth"** that's about to become federated.
- **Timestamps without timezone** (`TIMESTAMP` instead of `TIMESTAMPTZ`).
- **Money as float** instead of integer cents or arbitrary-precision decimal.
- **Strings where structured data belongs** (comma-separated IDs in a single column).

## Integration assumptions

- **Sync calls to an external API** that has a documented async option (webhooks, batch).
- **No retry / no circuit breaker** around external calls.
- **No timeout** on external calls (default is "wait forever").
- **Tight coupling to a vendor's response shape** with no anti-corruption layer.
- **Tight coupling to a vendor's identifier scheme** (using Stripe customer ID as primary key).

## Configurability / observability

- **Magic constants** that should be configurable (`100ms timeout`, `5 retries`, `7 days expiry`). At minimum, named constants; better, env-driven.
- **Hard-coded environment** (`if (process.env.NODE_ENV === 'production')` scattered in business logic).
- **No structured logging** on the new path — when this code misbehaves in prod, how will you debug?
- **No metric / no trace** for a load-bearing operation. Future you will be flying blind.
- **Errors logged but not categorized** — can't alert on the dangerous ones without alerting on every error.

## Compatibility / migration

- **Breaking change to a public API** without a deprecation path.
- **No versioning** on an external interface (REST endpoint, event schema, gRPC service).
- **Removed field still referenced by callers** — coordinate with consumers or stage the change.
- **Migration that's not safe to run on both old and new app code** during a rolling deploy.

## Lifecycle / cleanup

- **Resource created without a cleanup path.** New S3 bucket, new DB record, new background job — what removes them?
- **TTL not set on cache entries.** They live forever, including stale data.
- **Soft-delete column added but no compaction strategy.** Table grows forever.
- **Cron job with no off-switch.** Disabling requires a deploy.

## What this lens is NOT for

- ❌ "Design for 100M users when we have 100." Flag what's *likely* to change, not what's *possible* to change.
- ❌ "Add an interface in case we want to swap implementations." YAGNI applies; only flag if the swap is on the roadmap.
- ❌ Aesthetic refactors. If it's not going to break under foreseeable load / change, it's not in scope here.

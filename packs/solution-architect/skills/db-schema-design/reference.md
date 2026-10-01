# db-schema-design reference — paradigm matrix, keys, indexing, multitenancy, anti-patterns

## Paradigm-selection matrix (relational is the default; justify moving past it)

| Paradigm | Fits when | Access-pattern signal | Cost of choosing it |
|---|---|---|---|
| **Relational** (Postgres, MySQL) | transactional data, ad-hoc queries, joins, strong consistency | "we'll query this many ways, some not yet known"; integrity matters | vertical-scale ceiling (far off for most); needs sharding eventually at very high write volume |
| **Document** (Mongo, DynamoDB doc, Firestore) | entity read/written whole, varying shape per item, few cross-entity queries | "always fetch the whole order with its lines by order id" | ad-hoc cross-document queries are slow/absent; you design for the queries you know |
| **Key-value** (Redis, DynamoDB KV) | get/put by a single key, caching, sessions, very high throughput | "look up by exact id, nothing else" | no querying beyond the key; not a system of record alone |
| **Wide-column** (Cassandra, Bigtable) | massive write volume, time-series-ish, known query keys, linear scale | "billions of rows, query by partition+time, no joins" | one table per query pattern; data duplicated across tables; eventual consistency |
| **Graph** (Neo4j) | relationship traversal is the query (friends-of-friends, paths, recommendations) | "find all X connected to Y within N hops" | overkill for tabular data; operational maturity cost |
| **Time-series** (Timescale, Influx) | append-heavy metrics/events keyed by time, downsampling, retention | "ingest events, query ranges, roll up by window" | narrow purpose; pair with a relational store for the rest |

Polyglot is legitimate (Postgres for the system of record + Redis cache + a search index) — but each store needs its own access-pattern justification, and you now own the consistency between them.

## Key design

- **Surrogate vs natural (relational):** surrogate PK (`bigint` identity, or ULID/UUIDv7) by default — stable, opaque, join-friendly. Natural keys (email, SKU) get a `UNIQUE` constraint, not the role of clustered PK (they change, and they leak into URLs/logs).
- **Avoid random UUIDv4 as a clustered/primary key:** random order scatters inserts across the B-tree, causing page splits and write amplification. Use **UUIDv7/ULID** (time-ordered) when you need a UUID with ordered inserts, or a `bigint` sequence.
- **NoSQL partition + sort key:** derive from access patterns. Partition key must spread load — a low-cardinality or monotonically-increasing partition key creates a **hot partition**. Sort key co-locates and orders what's read together (e.g. PK=`customer_id`, SK=`order#<ts>` to list a customer's orders by time). One access pattern that doesn't fit the key shape = a new table or a secondary index, decided now.
- **Composite/natural uniqueness:** enforce real-world uniqueness (one active subscription per customer) with a partial/unique index, not app-code checks that race.

## Normalization / denormalization ladder

1. **Start at 3NF.** Each fact in one place; no update anomalies. This is the correct default for a system of record.
2. **Denormalize only for a named hot read**, and only after the normalized form is shown to be the bottleneck (or obviously will be). Examples: a counter cache (`order_count`), a duplicated display field to avoid a join on the top query, a materialized view.
3. **Every denormalization states its sync mechanism** — transaction, trigger, application code, or scheduled rebuild — and accepts the staleness window. A duplicated value with no sync owner *will* drift.
4. **NoSQL is denormalized by design** — you duplicate across items/tables to serve each access pattern; the "sync obligation" becomes a write-path responsibility (write to all copies, or accept eventual reconciliation).

## Indexing rules

- Index the columns that appear in `WHERE`, `JOIN`, and `ORDER BY` of **actual** queries.
- **Composite column order: equality predicates first, then the range predicate, then the sort column.** `WHERE tenant_id = ? AND created_at > ? ORDER BY created_at` → index `(tenant_id, created_at)`.
- A **covering index** (includes the selected columns) turns a hot read into an index-only scan — worth it for a top query, costly to maintain for a rare one.
- **Don't index low-selectivity columns alone** (a boolean, a 3-value status) — the scan is cheaper than the index hop; combine with a selective column instead, or use a partial index (`WHERE status = 'active'`).
- Every index taxes **every write** and consumes storage. The right count is "one per real query shape," not zero and not all-columns.
- Foreign-key columns are usually worth indexing (joins + cascade performance).

## Multitenancy isolation (decide early — expensive to reverse)

| Model | Isolation | Cost / blast radius | Fits |
|---|---|---|---|
| Shared table + `tenant_id` (+ row-level security) | logical, enforced by RLS/query | cheapest; a query bug = cross-tenant leak (see `threat-model`) | many small tenants, SaaS default |
| Schema-per-tenant | stronger; separate tables per tenant | migrations × N schemas; noisy-neighbor still shared | tens–hundreds of mid tenants |
| Database-per-tenant | strongest; separate DBs | highest ops cost; per-tenant backup/restore is a feature | few large/regulated/enterprise tenants |

State the choice and its trade. If shared-table, the `tenant_id` predicate is non-negotiable on every query and belongs in RLS, not developer discipline.

## Schema anti-pattern catalog

- **EAV (entity-attribute-value)** — rows of `(entity, attribute, value)` to be "flexible." Kills types, constraints, and queryability. Use real columns, or a typed `jsonb` column with documented shape and expression indexes — not a generic triple store.
- **The god table** — 60+ columns, half null for any given row, modeling several entities at once. Split by entity.
- **JSON-blob-as-schema-avoidance** — `jsonb` for everything to skip modeling, then unindexed queries digging into it. JSON is for genuinely variable/sparse sub-structure, with expression indexes on what you query.
- **Premature sharding** — operational complexity for scale you don't have. Vertical + read replicas + partitioning usually buy years first.
- **Index-everything / index-nothing** — both are failures; index the real query shapes.
- **Soft-delete everywhere without thought** — `is_deleted` flags leak into every query and every unique constraint; decide per table, and use partial indexes (`WHERE NOT is_deleted`).

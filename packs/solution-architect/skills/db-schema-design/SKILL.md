---
name: db-schema-design
description: Design a database schema from access patterns — paradigm chosen deliberately (relational/document/key-value/wide-column/graph), keys and partitioning driven by the actual queries, indexes mapped to predicates, money/time types right, and every read path verified to have a supporting access path. Use when the user is designing a data model, schema, or tables for a feature, choosing a database, or asks how to structure/store data.
---

# db-schema-design

Designs the storage layer **from the queries backward** — because a schema is right or wrong only relative to how it's read and written, and the most expensive schema mistakes are the access paths nobody designed for. Distinct from `data-contract` (the guarantee on a *published* dataset) and `api-contract-draft` (the sync interface): this is the table/collection/key design underneath. Hands evolution off to `migration-plan` and the published-dataset guarantee to `data-contract`.

## How to respond

1. **Collect the access patterns before drawing a single table.** The deliverable starts as a list: each read and write the feature needs, with **frequency**, **latency sensitivity**, **selectivity** (one row / a range / a scan), and **consistency need** (read-your-writes? eventual ok?). Ask at most 2 questions, spent on the highest-frequency query and the largest-growth entity. A schema designed from the entity diagram instead of the queries is how you get a clean model that can't serve its hottest path.

2. **Choose the paradigm deliberately, with a reason** (selection matrix in [`reference.md`](reference.md)). Relational is the correct default for most transactional features and needs no defense; reaching *past* it does. ✅ *"Document store — the entity is read and written whole, no cross-entity queries, and the shape varies per type"* — ❌ *"NoSQL because scale"* (scale is a property of access patterns and data size, not a vibe). For NoSQL especially, the access patterns *are* the schema — you cannot add a query later for free the way SQL lets you.

3. **Design keys from the queries.**
   - **Relational:** surrogate key (e.g. `bigint`/ULID) as PK by default; natural keys get a unique constraint, not the clustered PK. Avoid random UUIDv4 as a clustered/primary key — it scatters writes and splits pages; use a time-ordered ID (ULID/UUIDv7) when you need a UUID and ordered inserts.
   - **NoSQL:** partition key + sort key derived directly from the access patterns, chosen to spread load (no hot partition) and to co-locate what's read together. State the query each key shape serves.

4. **Normalize to 3NF, then denormalize only for a named read pattern — and name the sync obligation.** 3NF is the default because it makes writes correct and anomalies impossible. Every denormalization is a deliberate trade for a specific hot read, and it incurs a duplicate-keeping-in-sync debt that must be stated: ✅ *"Cache `order_count` on `customer` for the dashboard's top query; kept in sync by the order-write transaction / a trigger"* — ❌ a denormalized field with no answer to "what updates the copy?".

5. **Index for the actual predicates, joins, and sorts — not speculatively.** Every index pays a write cost and storage; an unused index is pure overhead. Rules (full set in [`reference.md`](reference.md)): index the columns in `WHERE`/`JOIN`/`ORDER BY` of real queries; **composite index column order is equality-first, then range, then sort**; consider a covering index for a hot read; don't index low-selectivity columns alone. Map each index to the query it serves — an index with no query is a guess.

6. **Get the types and constraints right at the schema, not in app code.** Money as integer minor units or `decimal`, **never float** (echoes `data-contract`); timestamps with explicit timezone (store UTC); enums as a constrained type or lookup table, not free strings; `NOT NULL` + defaults + `CHECK` + foreign keys express invariants the database enforces for every writer, including the ones you'll add later. Right-size types (don't `text` a 2-char country code).

7. **State the scale and multitenancy decisions.** Name the table that grows unbounded and its plan (partition by time, archive cold data); the partition/shard strategy if any (and why it's not premature); and the **multitenancy isolation model** (shared-table + `tenant_id` with row-level security / schema-per-tenant / db-per-tenant) with its trade — this is an early decision that's brutal to reverse, so it's explicit, not defaulted.

8. **Verify every access pattern has a supporting path, and emit with [`templates/schema-design.md`](templates/schema-design.md)** in one message: access-pattern table, paradigm + rationale, the schema (tables/collections with columns, types, keys, constraints), relationships/cardinality, indexes mapped to queries, scale + multitenancy decisions, and the **verification table** — each access pattern → the key or index that serves it, with any that fall to a full scan flagged. Evolution → `migration-plan`; published-to-consumers → `data-contract`.

## Useful references in this skill

- [`reference.md`](reference.md) — paradigm-selection matrix, key-design rules, the normalization/denormalization ladder, indexing rules, multitenancy options, and the schema anti-pattern catalog
- [`templates/schema-design.md`](templates/schema-design.md) — the design skeleton with access-pattern, schema, index, and verification tables

## Quality bar

- **Access patterns are listed before the schema**, with frequency and selectivity. A schema with no query list was designed blind.
- **The paradigm choice has a reason tied to access patterns** — and relational-by-default needs none while every move past it does.
- **Keys are justified by queries**, and no random UUIDv4 sits as a clustered PK without a noted reason.
- **Every index maps to a real query**; every denormalization names what keeps the copy in sync.
- **Money is never float, timestamps carry timezone, invariants are DB constraints** — not left to application discipline.
- **Multitenancy and the unbounded-growth table have explicit plans.** The expensive-to-reverse decisions are made on purpose.
- **The verification table shows each access pattern's supporting path**, with full scans flagged rather than hidden.

## When to use this skill

- ✅ Designing tables/collections/keys for a new feature or service
- ✅ Choosing a database paradigm for a known set of access patterns
- ✅ "How should I structure / store this data?" with real queries in mind
- ✅ Reworking a schema whose hot query has no supporting index

## When NOT to use this skill

- ❌ Governing a dataset other teams consume (quality SLAs, evolution policy) — that's `data-contract`
- ❌ The sync API/event shape over the data — that's `api-contract-draft`
- ❌ Executing a schema change on a live system (expand/backfill/contract) — that's `migration-plan`
- ❌ Picking a specific managed product (Aurora vs Cloud SQL) — that's `tech-comparison-matrix`; this designs the model, not the vendor

## Anti-patterns to avoid

- ❌ **Entity-first, query-never.** A beautiful normalized ER diagram whose top query needs four joins and a full scan. Design from the access patterns.
- ❌ **"NoSQL for scale" with no access-pattern argument.** NoSQL trades ad-hoc query flexibility for scale on *known* patterns; choosing it blind buys the downside without the upside.
- ❌ **UUIDv4 as the clustered primary key.** Random keys scatter inserts and fragment the index; use a time-ordered ID when you need a UUID.
- ❌ **EAV / the god table.** Entity-attribute-value "flexible" schemas and 80-column catch-all tables are queryability and integrity sold for a flexibility you'll regret.
- ❌ **JSON-blob-as-schema-avoidance.** Dumping everything in a `jsonb` column to skip design, then writing queries that dig into it with no index — schema design deferred, not avoided, and now unindexable.
- ❌ **Speculative indexing.** Indexing every column "to be safe" taxes every write and bloats storage; index the queries you have.
- ❌ **Float money / naked timestamps / stringly-typed enums.** The same three regrets as `data-contract`, baked in at the storage layer where they're hardest to fix.
- ❌ **Deferring the multitenancy decision.** Shared-table-vs-isolated is near-impossible to change after data lands; an unmade decision is the riskiest one.

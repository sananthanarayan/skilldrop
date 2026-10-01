# Schema-design template

Access patterns first, schema second, verification last — every query must end the document with a supporting path.

```markdown
# Schema design: {feature / domain}

**Paradigm:** {relational | document | key-value | wide-column | graph | time-series}
**Rationale:** {tied to the access patterns below — relational needs none; anything else justifies}
**Engine (if decided):** {Postgres 16 | DynamoDB | …} `[assumption if not confirmed]`

## Access patterns (the spec the schema is judged against)

| # | Query / write | R/W | Frequency | Selectivity | Latency | Consistency |
|---|---|---|---|---|---|---|
| Q1 | get order with lines by order id | R | very high | 1 row + children | <50ms | read-your-writes |
| Q2 | list a customer's orders, newest first | R | high | range | <200ms | eventual ok |
| W1 | create order + lines | W | high | — | — | atomic |

## Schema

### {table / collection: orders}

| Column | Type | Null | Key/constraint | Notes |
|---|---|---|---|---|
| id | bigint / ULID | no | PK | surrogate; time-ordered |
| customer_id | bigint | no | FK → customers(id), indexed | |
| total_minor | bigint | no | CHECK (>= 0) | minor units, currency below — never float |
| currency | char(3) | no | CHECK (ISO-4217) | |
| status | text | no | CHECK in (pending,paid,shipped,cancelled) | enum, not free string |
| created_at | timestamptz | no | default now() | UTC |

{Repeat per table/collection. For NoSQL: state PK (partition) + SK (sort) and the access pattern each serves.}

## Relationships

- customers 1 —< orders 1 —< order_lines  (cascade: delete order → delete its lines)
- {cardinality + cascade/restrict per relationship}

## Indexes (each maps to a query)

| Index | Columns (order matters) | Serves | Type |
|---|---|---|---|
| idx_orders_customer_created | (customer_id, created_at) | Q2 (equality then sort) | btree |
| pk_orders | (id) | Q1 | primary key (clustered/index-organized only on engines that support it — Postgres heaps don't) |

{Note any covering/partial index and why. No index without a query.}

## Denormalizations (if any)

| Field | On | For query | Kept in sync by |
|---|---|---|---|
| order_count | customers | dashboard top read | order-write transaction |

## Scale & multitenancy

- **Unbounded-growth table:** {orders} — plan: {partition by created_at month; archive > 24mo to cold storage}.
- **Partition/shard:** {none yet — vertical + read replica suffices to ~Nx; revisit at {trigger}} or {strategy + why not premature}.
- **Multitenancy:** {shared-table + tenant_id + RLS | schema-per-tenant | db-per-tenant} — trade: {…}. `tenant_id` predicate enforced by {RLS policy}.

## Verification — every access pattern has a path

| # | Supported by | Full scan? |
|---|---|---|
| Q1 | pk_orders + FK index on lines | no |
| Q2 | idx_orders_customer_created | no |
| W1 | insert; FK indexes present | no |

⚠ {Any pattern with no supporting index/key — flag it and resolve before build.}

## Evolution

- Migrations / rollout of changes → `migration-plan`.
- If this data is published to other teams → wrap it in a `data-contract`.
```

# data-contract reference — quality dimensions, evolution matrix, field semantics

## Data-quality dimension catalog

Each dimension on the contract gets: a **threshold**, a **check** (how/when measured), and a **breach action**. Pick the dimensions that matter for this asset; mark the rest n/a with a reason.

| Dimension | What it guarantees | Threshold example | Check | Breach action examples |
|---|---|---|---|---|
| **Freshness** | data is recent enough to trust | partition D lands by 06:00 D+1 | scheduler SLA / landing-time monitor | page owner; mark stale on the dashboard |
| **Completeness** | nothing silently missing | row count within ±10% of trailing-7d median; all partitions present | post-load count check | quarantine partition; block downstream |
| **Validity** | values satisfy field constraints | ≥99.9% rows pass per-field rules | constraint suite per load | reject load; alert; route bad rows to DLQ |
| **Uniqueness** | the key is actually unique | `event_id` 100% unique | dup-count query | breach = contract violation, not silent dedup |
| **Consistency** | cross-field/cross-table invariants hold | `ends_at` ≥ `starts_at`; FK resolves | invariant assertions | alert; hold publish |
| **Distribution / drift** | columns consumers model don't shift unannounced | null-rate, cardinality, mean within historical band | drift monitor vs baseline | alert consumers; investigate before publish |
| **Timeliness of correction** | how fast a known-bad load is fixed | corrected within {N}h of detection | incident clock | comms to consumers (→ `incident-comms`) |

A dimension with no breach action is decoration. The breach action is the part consumers actually rely on.

## Schema-evolution safe/breaking matrix (for DATA consumers)

"Breaking" here means: a downstream query, pipeline, or trained model could silently produce wrong results or fail. Data consumers are more fragile than API clients — `SELECT *`, positional reads, and models that learned a column's distribution all break in ways HTTP clients don't.

| Change | Safe? | Notes |
|---|---|---|
| Add optional/nullable column **with** default or documented null-meaning | usually safe | still breaks strict `SELECT *` schema checks — notify |
| Add `NOT NULL` column without default | **breaking** | every existing writer fails |
| Remove or rename a column | **breaking** | rename = remove + add; positional/`*` consumers break |
| Change type (even "widening") | **breaking** | int→float shifts joins, aggregations, model features |
| **Change the meaning** behind a stable name+type | **breaking — the silent killer** | gross→net, UTC→local, cents→dollars: no validator catches it; only the contract can |
| Narrow an enum (remove an allowed value) | **breaking** | consumers branching on it lose a case |
| Widen an enum (add an allowed value) | maybe breaking | breaks consumers with exhaustive switches; declare enum open/closed |
| Tighten a constraint (e.g. now `NOT NULL`) | **breaking** | historical rows / lenient writers violate it |
| Loosen a constraint | usually safe | but consumers assuming the old guarantee may break |
| Change partitioning / sort | **breaking for performance** | consumer queries may table-scan or time out |

**Every breaking change requires:** version bump → deprecation window (name it, e.g. 30 days or until all registered consumers ack) → notification to the registered consumer list → both versions available during the window where feasible. This mirrors `migration-plan`'s expand/contract — apply it to the schema.

## Field-semantics rules (the cents-vs-dollars firewall)

Every field on the contract states:
- **Unit** for any quantity — currency + minor/major units, time unit, byte/bit, percentage-as-0-1-vs-0-100. The single most common silent data bug is a unit assumption.
- **Allowed values** for any categorical — the full enum, open or closed.
- **Null semantics** — is `null` "unknown", "not applicable", or "zero"? These are three different facts; pick one and write it.
- **Timezone** for any timestamp — UTC unless stated; name the zone, never leave it implicit.
- **Meaning** — one line a new consumer reads instead of guessing. "`status`: lifecycle state of the order, see allowed values" beats inferring from the name.
- **Identity** — which field(s) uniquely identify a row, and whether IDs are stable across reloads.

# Data-contract template

A dataset is a product. This is its label, its warranty, and its change policy.

```markdown
# Data contract: {asset name}

**Asset:** {warehouse table | Kafka topic | file feed | view} — `{fully.qualified.name}`
**Owner:** {team/role} · **Contact / on-call:** {channel}
**Producer:** {pipeline/service} · **Update mechanism:** {batch | streaming | CDC}
**Version:** {v1} · **Status:** {proposed | active | deprecated}

## Consumers (defines what "breaking" means)

| Consumer | Team | Usage | Notify on change |
|---|---|---|---|
| {dashboard/model/pipeline} | {team} | {what they read it for} | {channel} |

⚠ {Flag any unknown/unregistered consumers — a change can't be safely made until known.}

## Schema (types + semantics)

| Field | Type | Req? | Null means | Unit / allowed values | Meaning |
|---|---|---|---|---|---|
| `event_id` | string | required | — | opaque UUID | unique row identity, stable across reloads |
| `amount` | int64 | required | — | minor units (cents), {currency} | net charged after discounts |
| `country` | string | optional | unknown | ISO-3166-1 alpha-2, open enum | billing country |
| `occurred_at` | timestamp | required | — | UTC, ISO-8601 | when the event happened (not when ingested) |

**Identity:** {field(s) that uniquely identify a row}
**Grain:** {one row per … }

## Quality SLAs

| Dimension | Threshold | Check | Breach action | Met today? |
|---|---|---|---|---|
| Freshness | partition D by 06:00 D+1 | landing monitor | page owner | ✅ / aspirational |
| Completeness | rows within ±10% of 7d median | post-load count | quarantine partition | … |
| Validity | ≥99.9% pass field rules | constraint suite | reject load, alert | … |
| Uniqueness | `event_id` 100% unique | dup query | contract breach | … |
| Distribution | null-rate/cardinality in band | drift monitor | alert consumers | … |

{Mark each "Met today?" honestly: ✅ currently met, or "aspirational — pipeline does not yet meet this".}

## Schema-evolution policy

- Safe (notify only): {additive nullable columns with documented null-meaning}
- Breaking (version bump + deprecation window + consumer ack): removals, renames, type changes, **meaning changes under a stable name**, enum narrowing, constraint tightening, partition changes.
- Deprecation window: {e.g. 30 days, or until all registered consumers ack}; both versions live during the window where feasible.
- Meaning-change clause: a field's documented meaning is part of the contract; changing it (e.g. gross→net) is breaking even if name and type are unchanged.

## Delivery

- **Location / format:** {path or topic} · {Parquet | Avro | JSON}
- **Partitioning:** {scheme}
- **Cadence:** {hourly | daily 06:00 | continuous}
- **Streaming only:** delivery {at-least-once → dedupe on identity}; ordering {per-key | none}; retention {N days}
- **Register as a consumer:** {how — so breaking-change notices reach you}

## Classification & retention

| Field(s) | Classification | Retention | Residency |
|---|---|---|---|
| {field} | {PII / sensitive / public} | {period} | {constraint or none} |

## Open questions

- {unknowns blocking sign-off — e.g. undiscovered consumers, an SLA not yet measurable}
```

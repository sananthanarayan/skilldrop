---
name: data-contract
description: Draft a data contract for a dataset, table, or event stream consumed by others — schema with per-field semantics and units, measurable quality SLAs (freshness, completeness, validity, distribution), a schema-evolution policy that says what breaks consumers, a named owner, and PII classification. Use when the user is publishing a dataset/table/topic other teams depend on, needs a data contract, or wants to stop downstream pipelines breaking on silent schema or quality changes.
---

# data-contract

Treats a dataset, table, or topic as a **product with an owner and a guarantee** — the agreement a producing team makes to everyone reading their data. Distinct from `api-contract-draft` (synchronous request/response + webhook interfaces): this governs *data at rest and in motion* — the warehouse table, the Kafka topic, the daily export — where the failure mode isn't a 500, it's a downstream model silently trained on a column whose meaning changed last Tuesday.

## How to respond

1. **Establish producer, consumers, and the asset.** What dataset (table / topic / file feed), who produces it, and **who consumes it** — because the consumer list is what makes a change "breaking". Ask at most 2 questions, spent on the asset's update mechanism (batch / streaming / CDC) and whether any consumer is outside the producing team's control (another team, a partner, a trained model). A dataset with unknown consumers can't have a contract — surfacing that is the first value.

2. **Specify schema with semantics, not just types.** Types prevent crashes; semantics prevent silent wrongness. Every field gets: name, type, **nullability**, **unit or allowed-values**, and a **one-line meaning**. ✅ *"`amount` — int64, not null, minor currency units (cents), the net charged after discounts"* — ❌ *"`amount` — integer"* (cents or dollars? gross or net? the model that assumed dollars is now off by 100×). Mark every field's `[required]` vs `[optional]` and whether `null` is a valid value distinct from absent.

3. **Set quality guarantees as measurable SLAs** (catalog in [`reference.md`](reference.md)) — each with a threshold, a check, and a **breach action**:
   - **Freshness** — max acceptable lag ("partition for day D lands by 06:00 D+1")
   - **Completeness** — expected volume / no gaps ("row count within ±10% of trailing-7-day median; no missing partitions")
   - **Validity** — % rows passing field constraints ("≥99.9% of `email` rows match the format")
   - **Uniqueness** — the key that's actually unique ("`event_id` unique; duplicates are a contract breach, not a dedup hint")
   - **Distribution** — drift bounds on the columns consumers depend on ("`country` cardinality and null-rate within historical band")
   A quality SLA without a breach action ("page the producer" / "quarantine the partition" / "alert consumers") is a wish; name the action.

4. **Write the schema-evolution policy — the section that earns the contract.** State precisely what's safe and what isn't, *for data consumers specifically*: adding an optional column is usually safe; adding a `not null` column without a default breaks every writer; **changing a field's meaning while keeping its name and type is the silent killer** and is always breaking; removing or renaming is breaking; narrowing an enum is breaking, widening may be. Every breaking change requires a **version bump + a deprecation window + consumer notification** — and the contract names the window (e.g. "30 days, or until all registered consumers ack").

5. **Make ownership and classification first-class.** Named owner (team/role, not a person), an on-call or contact, PII/sensitivity classification per field, retention period, and residency if constrained — the same discipline as `nfr-spec`, scoped to this asset. An unowned dataset is an incident waiting for a quarter-end.

6. **Specify delivery.** Where it lives, format (Parquet/Avro/JSON), partitioning scheme, update cadence, and how a consumer registers as a dependent (so the breaking-change notification has an address list). For streams: delivery semantics (at-least-once default — consumers dedupe on the unique key), ordering guarantees, and retention.

7. **Emit with [`templates/data-contract.md`](templates/data-contract.md)** in one message: header (asset, owner, consumers), schema table with semantics, quality SLA table with breach actions, evolution policy, delivery spec, classification. Where the asset already exists, note which guarantees are *aspirational* vs *currently met* — an honest contract beats a flattering one.

## Useful references in this skill

- [`reference.md`](reference.md) — the data-quality dimension catalog, the schema-evolution safe/breaking matrix, and field-semantics rules
- [`templates/data-contract.md`](templates/data-contract.md) — the contract skeleton with schema and SLA tables

## Quality bar

- **Every field has a meaning and a unit/allowed-values**, not just a type. The cents-vs-dollars class of bug is designed out at contract time.
- **Every quality SLA has a threshold, a check, and a breach action.** "High quality" is not an SLA; "freshness < 6h, checked hourly, breach pages the owner" is.
- **The evolution policy names the silent killer** — meaning-change-under-stable-name — as breaking. Most contracts miss it and most data incidents are it.
- **Consumers are enumerated**, so "breaking" is defined and notifications have an address. Unknown consumers are flagged, not assumed away.
- **The asset has a named owner and per-field classification.** No owner, no contract.
- **Existing-asset contracts mark aspirational vs met.** Claiming a freshness SLA the pipeline doesn't hit is how the contract loses its authority on day one.

## When to use this skill

- ✅ Publishing a table/topic/feed other teams or models will depend on
- ✅ "We need a data contract for X" / stopping downstream breakage from schema drift
- ✅ Formalizing the guarantee on a dataset that's already widely consumed
- ✅ A data-mesh / data-as-a-product initiative needing per-asset contracts

## When NOT to use this skill

- ❌ A synchronous REST/RPC API or webhook — that's `api-contract-draft`
- ❌ The physical schema migration (expand/backfill/contract) — that's `migration-plan`
- ❌ System-wide NFRs for a service — that's `nfr-spec`; this is one data asset's guarantee
- ❌ A private dataset with exactly one consumer inside the same team — a comment in the code may suffice

## Anti-patterns to avoid

- ❌ **Types without semantics.** `status: string` with no allowed-values list means every consumer invents their own set and one of them is wrong.
- ❌ **Quality as an adjective.** "Clean, reliable data" — unmeasurable, unenforceable, unfalsifiable. Dimensions with thresholds or nothing.
- ❌ **Ignoring meaning-change.** Renaming the *concept* behind `revenue` from gross to net while the column name and type hold — the most expensive data bug there is, and zero schema validators catch it. The evolution policy must.
- ❌ **The orphan dataset.** No owner, no consumer list — so no one can be paged and no one can be warned. That's not a product, it's a liability.
- ❌ **Aspirational SLAs on a pipeline that misses them.** A freshness promise the batch job blows nightly trains consumers to ignore the whole contract.
- ❌ **Treating additive as automatically safe.** A new `not null` column with no default breaks every existing writer; a new column can break a `SELECT *` consumer's schema check. Additive ≠ free in data.

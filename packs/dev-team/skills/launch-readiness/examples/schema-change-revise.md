# Worked example — schema change that comes out REVISE

## Input given to the skill

> Go/no-go for release `orders-v4.2`. It splits `orders.address` into `shipping_address_id`
> pointing at a new `addresses` table. We followed the migration plan
> (docs/migrations/orders-address.md): expand and backfill are done in staging, and dual-write
> is behind the flag `orders.address_split`. Rollback is "turn the flag off". It was rehearsed
> in staging on 2026-09-28 (log: ci/run/88213). The p99 target for order reads is 120ms, and
> the canary at 5% shows 96ms (grafana/d/orders-canary). The existing `orders-5xx` alert
> covers this. Release notes are drafted in PR #977. Plan is 5% → 50% → 100% over three days.

---

# Launch readiness — orders-v4.2 (address split)

**Change:** release `orders-v4.2` · **Reach:** 5% → 50% → 100% over 3 days · **Release owner:** Orders tech lead
**Assessed:** 2026-10-01 · **Inputs:** migration plan, staging rollback log, canary dashboard, PR #977

## New failure modes

| # | Failure mode | Who is hurt | Reversible? |
|---|---|---|---|
| F1 | Dual-write diverges: an order is saved with an `addresses` row that doesn't match `orders.address` | Customers shipped to the wrong address | Partly. Data can be fixed, parcels already sent cannot |
| F2 | The read path picks the new column before the backfill is complete for that tenant | Customers who see a blank address at checkout | Yes, by turning the flag off |
| F3 | The extra join pushes order reads past p99 under full load | All checkout users | Yes, by turning the flag off |

## Checks

| # | Check | Covers | Status | Evidence | Owner |
|---|---|---|---|---|---|
| 1 | Rollback | all | met | Flag-off rehearsed in staging, ci/run/88213. While the old column is still written, flag-off loses no data | Orders on-call |
| 2 | Detection | F1–F3 | **not met** | `orders-5xx` catches F3 errors only. Nothing detects F1 divergence or F2 blank reads, because both return 200 | Orders on-call |
| 3 | Response | F1–F3 | **not met** | There is no runbook entry for divergence. `orders-5xx` has a runbook entry, but it does not mention the flag | Orders on-call |
| 4 | Quality targets | F3 | met | Canary p99 96ms against a 120ms target at 5%, grafana/d/orders-canary | Orders tech lead |
| 5 | Data & privacy | — | n/a — no new personal data. Address data moves between tables, and retention and processors are unchanged | Migration plan §2 | Data protection lead |
| 6 | Comms | — | met | Release notes drafted in PR #977. No customer-visible change | Orders tech lead |
| 7 | Exposure | — | met | Staged 5% → 50% → 100% behind `orders.address_split` | Release owner |

## Open items

- Row 2: add a reconciliation metric for dual-write divergence, and an alert on any non-zero count, plus an alert on blank-address reads. Orders on-call, before the 5% → 50% step. Hand off to `observability-plan`.
- Row 3: add a runbook entry for "divergence alert fires" (flag off, then run the reconciler), and add the flag to the `orders-5xx` entry. Orders on-call, same deadline. Hand off to `runbook-generator`.

## Verdict

**REVISE.** Row 2 is not met: the two failure modes that do lasting damage (F1, F2) return 200, so nothing would detect them. Fix rows 2 and 3, then run readiness again.

---

**Why this is a good output:** the rollback is genuinely in place, so the verdict is REVISE and
not BLOCKED. The report notices that an existing alert covering the change only catches the
failure that is easiest to undo. It does not draft the alert or runbook itself; it names the
gap, the owner and the hand-off.

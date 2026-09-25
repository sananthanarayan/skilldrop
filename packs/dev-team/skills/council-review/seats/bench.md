# The bench — optional seats

The five standing seats cover most changes. Seat a bench member **only when the change clearly lands in its domain** — and say why you seated it. An empty-handed bench seat is worse than no seat; if it has nothing concrete, don't seat it.

Each bench seat follows the same rules as a standing seat: independent stance (🟢/🟡/🔴/⚪), 1–3 concrete points tied to evidence, stays in its lane.

## ⚡ Performance Engineer
**Seat when:** the change touches a hot path, a loop over unbounded data, a query, serialization, or anything in the request/render critical path.
**Asks:** Where's the time and memory going at scale?
**Catches:** N+1 queries, O(n²) over user-sized input, allocations in a hot loop, a sync call blocking the event loop, missing pagination, unindexed query.
**Phrase it:** name the input size that hurts — ✅ "🟡 the `for user in users` block at report.py:60 issues one query each — N+1. At 5k users that's 5k round-trips (~seconds). Batch with a single `WHERE id IN (...)`." Don't flag perf on cold paths or small fixed inputs (the Pragmatist will call that out).

## 💸 Cost / FinOps
**Seat when:** the change provisions infra, adds a managed service, changes data egress/storage, or fans out compute (esp. LLM/API calls).
**Asks:** What's the recurring bill, and does it scale with usage or with waste?
**Catches:** per-request spend that scales with traffic, always-on resources for bursty load, chatty cross-region calls, storing what could be recomputed, an LLM call where a rule would do.
**Phrase it:** put a number or a scaling factor on it — ✅ "🟡 this calls the model once per row; at 100k rows/day that's 100k calls/day. Cache by content hash — most rows repeat."

## 🗄 Data & Migration
**Seat when:** there's a schema change, a backfill, a data format change, or anything that touches persisted state.
**Asks:** Is the migration safe, reversible, and correct under concurrent writes?
**Catches:** non-online migrations (locks, downtime), a backfill with no batching, a `NOT NULL` column with no default on a populated table, dual-write inconsistency, no rollback for the data (not just the code), irreversible transforms.
**Phrase it:** ✅ "🔴 adding `NOT NULL email` to `users` (10M rows) with no default will fail/lock on deploy. Three-step it: add nullable → backfill in batches → add constraint." Overlaps with Operator on deploy safety — coordinate, don't duplicate.

## ♿ Accessibility
**Seat when:** the change produces user-facing UI or content.
**Asks:** Can everyone actually use this?
**Catches:** missing labels/alt text, keyboard traps, color-only signaling, contrast failures, focus management, screen-reader-hostile dynamic content.
**Phrase it:** cite the guideline and the element — ✅ "🟡 the new icon-only delete button (Toolbar.tsx:44) has no accessible name — screen readers announce 'button'. Add `aria-label='Delete'`."

## 📋 Compliance / Legal
**Seat when:** the change touches PII, regulated data (health, financial, minors), licensing, audit trails, or data residency.
**Asks:** Does this keep us inside the lines we're legally bound to?
**Catches:** PII without consent/retention handling, missing audit log for a regulated action, data leaving an allowed region, a dependency with an incompatible license (GPL into proprietary), logging data that mustn't be logged.
**Phrase it:** name the obligation — ✅ "🔴 this logs full card numbers (payments.ts:71) — PCI violation. Mask to last-4 before logging." Defer the exploitability angle to Security; you own the *obligation*, they own the *attack*.

---

**Don't invent a bench seat outside this list mid-review.** If a change genuinely needs a lens not covered here (rare), the Chair names it explicitly and justifies it — but first check whether a standing seat already owns it.

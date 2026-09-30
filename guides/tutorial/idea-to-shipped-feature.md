---
title: From idea to shipped feature
summary: A product idea moves through all four lifecycle loops — discover, design, build, operate — with each gate refusing until its conditions are met.
kind: tutorial
---

# From idea to shipped feature

A customer request becomes a shipped feature. This walkthrough takes one idea through all four lifecycle loops — `discover`, `design`, `build`, `operate` — and shows a real refusal at every gate. The refusals are the point: a gate that always passes is decoration.

Install all four loops:

```bash
npx skilldrop-cli install --loop discover design build operate
```

The feature: *"Let users export their data as a CSV."*

---

## The situation

A product manager receives the same request from three enterprise customers in a quarterly review: they need to export their account data for internal reporting. The PM wants to take it through the full loop sequence — not because the feature is complex, but because it touches data export, which means security and compliance matter.

---

## Loop 1 — `discover` (G0: human ratification)

### `signal-to-requirement`

The PM runs `signal-to-requirement` with the three customer requests as input. The skill surfaces ambiguities: which data, which users, what format, what size limits, what latency expectation?

After a short interview, the structured requirement:

> "Authenticated users can export all data associated with their account as a CSV file. Export must complete within 60 seconds for accounts with fewer than 100,000 rows. Files are available for 24 hours after generation. No PII from other accounts may appear in the file."

### `prd-generator`

The PM runs `prd-generator` with the requirement. The PRD draft includes:

- User story: "As an account owner, I can download my data as CSV so that I can use it in my own reporting tools."
- Acceptance criteria: users can trigger export, receive a download link, and the file contains only their data.
- Out of scope: real-time exports, partial exports by date range.

### `metrics-plan`

`metrics-plan` defines success metrics: download completion rate (target: >98%), zero data-leakage incidents, p95 export time <45s for accounts under 100k rows.

### Gate G0 — REVISE, then READY

The gate reads the PRD and acceptance criteria.

First run returns `REVISE`:

```
G0 REVISE
Acceptance criteria are under-specified. "Contains only their data" is not
testable — the criteria must name the tables/fields in scope and explicitly
state that cross-account rows are rejected at the query layer, not filtered
after retrieval.
```

The PM tightens the criteria: the export query is scoped to `WHERE account_id = :current_user_account_id`, cross-account filtering is enforced at the query layer not application layer, and the field list is enumerated. Re-running:

```
G0 READY
Requirement is specific and testable. Proceed to design.
```

---

## Loop 2 — `design` (G1: council-review)

### `architecture-diagrams`

The engineer runs `architecture-diagrams` with the ratified requirement. The skill proposes the export pipeline:

1. User triggers export via API endpoint
2. Job is enqueued in a background job queue (async, not synchronous — avoids 60s HTTP timeout risk)
3. Job queries the database, streams rows to S3 as CSV
4. Pre-signed URL (24h expiry) is sent to the user by email

### `adr-generator`

`adr-generator` records the key decision: async job queue over synchronous HTTP response.

> **ADR-012: Use async export jobs over synchronous response**
> Context: CSV exports can take up to 60s for large accounts. A synchronous HTTP response risks timeout at the load balancer or client.
> Decision: Enqueue a background job. User receives an email with a pre-signed S3 URL when the export is ready.
> Consequences: Users wait for an email rather than a direct download. Export status polling endpoint needed.

### `threat-model`

`threat-model` runs against the architecture and flags a risk:

> **Risk: Pre-signed URL expiry window is 24 hours.**
> A URL forwarded by mistake (e.g., shared in a support ticket) gives access to the user's data for up to 24 hours. Consider a shorter expiry (4h) with a re-generation endpoint, or add download event logging so leaked URLs are detectable.

The ADR is updated: expiry shortened to 4 hours; a download event log is added to the architecture.

### Gate G1 — PROCEED WITH CONDITIONS

`council-review` runs with devils-advocate, security-reviewer, and code-quality agents:

```
G1 PROCEED WITH CONDITIONS

security-reviewer: The pre-signed URL expiry fix addresses the primary data
  exposure risk. Condition: every export generation and every download must
  be written to an immutable audit log (account_id, timestamp, IP, action).
  This is non-negotiable for enterprise compliance.

devils-advocate: The async model is correct but the email delivery path is
  now a dependency. Condition: document what happens if the email fails —
  users need a way to retrieve their export without re-triggering.
  A "recent exports" page in the UI satisfies this.

code-quality: No objection. The ADR captures the trade-offs clearly.
```

The team adds the audit log to the architecture and a "recent exports" page to the PRD. Re-gating:

```
G1 READY
Conditions met. Proceed to build.
```

---

## Loop 3 — `build` (G2: pre-merge-review)

### `user-story-splitter`

`user-story-splitter` breaks the PRD into four implementation stories:

1. **Job queue**: background worker, job schema, retry logic
2. **S3 upload**: streaming CSV writer, pre-signed URL generation, 4h expiry
3. **Email notification**: trigger on job completion, link in email, fallback to "recent exports" page
4. **Audit log**: immutable log writes on export trigger and download events; read path for compliance team

### `feature-implement-loop`

Each story runs through the `build` loop: implement → test → `pre-merge-review`.

Stories 1–3 pass `pre-merge-review` on first submission.

Story 4 (audit log) is blocked:

```
G2 BLOCKED

code-quality: The audit log write has no test coverage for the failure path.
  If the log write fails, the current implementation silently swallows the
  error and the export proceeds. For an immutable compliance log this is
  incorrect — a log write failure must either halt the export or raise a
  high-severity alert. Neither is implemented.
```

The engineer adds a test for the audit log failure path and makes the export fail closed (job is marked failed; user sees an error and is asked to retry). Re-gating:

```
G2 READY
Audit log failure path is tested and handled correctly. Proceed to ship.
```

The feature ships in the next release.

---

## Loop 4 — `operate` (G3: postmortem closes the loop)

### Post-ship monitoring

Two weeks after launch, `ai-usage-report` tracks adoption: 340 exports in the first two weeks, 99.1% completion rate, p95 latency 38s. The "recent exports" page is used in 12% of sessions, confirming the fallback was worth building.

### Incident

On day 18, a silent failure pattern emerges: export jobs for accounts with files attached (stored as binary BLOBs) fail at the streaming step with no user notification. The 500s are logged but no alert fires because the job failure rate (0.3%) is below the alert threshold.

`incident-response` triages the issue: the CSV writer does not handle binary columns — it attempts to encode BLOBs as UTF-8 and silently fails. Affected accounts have files attached. The fix: skip binary columns with a warning in the CSV header.

### `postmortem-generator`

```
G3 PROCEED

Postmortem filed. Runbook delta:
- Add BLOB column handling to the export worker's known-failure section
- Add a per-job completion alert (not just aggregate rate) to the
  detection signals — silent per-job failure was the root cause of the
  delay in detection
- Update threat model: binary columns in user data were not enumerated
  as a risk surface
Routing delta to runbook-generator for update.
```

The updated runbook and a new threat model entry (binary column handling) are committed. Gate G3 closes the loop.

---

## What the gates prevented

| Gate | What it blocked | What would have happened without it |
|---|---|---|
| G0 REVISE | Untestable acceptance criteria ("contains only their data") | Query-layer enforcement would have been an assumption, not a requirement — cross-account data leakage possible |
| G1 PROCEED WITH CONDITIONS | Missing audit log; no fallback if email fails | No compliance audit trail; users with failed emails would have no way to retrieve their export |
| G2 BLOCKED | Audit log failure path silently swallowed | A log write failure during export would have been invisible — compliance gap, no alert |
| G3 postmortem delta | Binary column handling not in threat model; per-job alerting missing | Next binary-column incident would have gone undetected for the same reason |

The gates did not slow the feature down. G0 REVISE caught a testability gap in the acceptance criteria — that conversation would have happened anyway, just later and more expensively in code review. G1's conditions added the audit log before build started, not after a compliance audit found it missing. G2's block caught a silent failure mode in a compliance-critical path. G3 closed the loop on a gap the threat model did not anticipate.

# Worked example — critique of a design-doc excerpt

Input → output oracle for `doc-critique`. Shows local, doc-quoting findings with
paste-able fixes — reviewing whether the doc *made its case*, not re-debating the topic.

## Input (excerpt of a design doc under review)

> ## TL;DR
> We will build an innovative, scalable notification service to leverage our
> existing infrastructure and deliver best-in-class user engagement.
>
> ## Approach
> The service consumes events and sends notifications. It will be highly
> available and performant. We considered several options and chose a
> queue-based design because it is the industry standard.
>
> ## Rollout
> We will roll it out to all users.

## Output (the critique)

**Verdict: not ready to circulate — 1 blocker, 2 major, 1 minor.** The doc asserts conclusions it never earns; a reader can't tell what's being built or why this shape.

🟥 **Blocker — the decision has no rationale (§ Approach).** Quoted: *"chose a queue-based design because it is the industry standard."* "Industry standard" is not a reason; it hides the actual tradeoff. *Fix:* replace with the decision's real driver — e.g. "chose a queue so a downstream outage buffers events instead of dropping them; the alternative (synchronous fan-out) loses notifications when a provider is down." Name the alternative and why it lost.

🟧 **Major — TL;DR is adjectives, not content (§ TL;DR).** Quoted: *"innovative, scalable … leverage … best-in-class user engagement."* Five value-words, zero facts — a reader learns nothing about scope. *Fix:* state what it does and the one number that matters: "A queue-backed service that delivers email/push notifications from domain events, targeting < 5s p95 delivery for 1M events/day."

🟧 **Major — unfalsifiable quality claims (§ Approach).** Quoted: *"highly available and performant."* No SLO, so nothing can be reviewed or later checked. *Fix:* commit numbers — availability target (e.g. 99.9%), p95 latency, throughput — or move them to an explicit "Open questions" list if unknown.

🟨 **Minor — rollout has no stages or guardrail (§ Rollout).** Quoted: *"roll it out to all users."* No canary, no rollback trigger. *Fix:* a 2–3 line staged plan (1% → 10% → 100%) and the metric that halts it (delivery-failure rate > X%).

## Why this passes the quality bar

Severity is calibrated (one blocker). Every finding is **local** and **quotes the doc verbatim** (the audit trail that it was actually read), the fixes are paste-able, and it critiques the *doc's* case-making — it does not re-argue whether a queue is the right architecture.

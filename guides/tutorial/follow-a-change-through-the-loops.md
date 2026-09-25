---
title: Follow one change through the loops
summary: A single realistic change — API rate limiting — walked from a stakeholder complaint to a closed incident, showing what each stage produces and what each gate actually refuses.
kind: tutorial
---

# Follow one change through the loops

One change, all four loops, start to finish. The point is not the artifacts — it is seeing
**what each gate refuses**, because a gate that never refuses anything is decoration.

Install what you need as you go, or take it all up front:

```bash
npx skilldrop-cli install --loop discover design build operate
```

The change: *"Enterprise customers keep hitting our API limits and complaining."*

---

## Loop 1 — `discover`

### `gather` → `structure` → `specify` → **G0 (human)**

**gather.** The signal arrived as a complaint from an account manager, so this is a
conversation, not a journey map. Run [`requirements-interview`](../../skills/requirements-interview/SKILL.md).
It comes back with the thing that matters: nobody has said *which* limit, *which* customers,
or what "keep hitting" means numerically.

**structure.** Run [`brief-intake`](../../skills/brief-intake/SKILL.md). Every field gets a tag:

```
Problem     [explicit]  "Enterprise customers hit API limits" — AM, Slack, 12 Sep
Scope       [inferred]  the public REST API — nobody said so
Threshold   [missing]   no current limit documented
Impact      [missing]   how many customers, how often
```

> 🚩 **Missing for downstream:** `prd-draft` will refuse to write requirements without
> a measured threshold and an affected-customer count.

**This is the loop doing its job.** Two `[missing]` tags are worth more than a confident PRD
built on a guess. Go get the numbers: 3 customers, ~40 rejections/day, current limit 100 req/min.

**specify.** Run [`prd-draft`](../../skills/prd-draft/SKILL.md) on the now-complete brief.

**G0 — human.** A person ratifies that *tiered limits per plan* is the problem worth solving.
No script can tell you that you solved the wrong problem well, which is why this gate is a
person and why an agent running non-interactively emits `BLOCKED: need ratification` rather
than ticking it itself.

**What G0 refuses:** an unratified brief. If your stakeholder says *"actually, they want
burst capacity, not a higher ceiling"* — that is `RECONSIDER`, and it **leaves the loop**.
Re-briefing cannot fix a wrong problem.

---

## Loop 2 — `design`

### `constrain` → `shape` → `threat` → **G1 (review)** → `record`

**constrain first, always.** [`nfr-spec`](../../skills/nfr-spec/SKILL.md) before any
structure: *limit decisions add ≤5ms p99; the limiter survives a Redis failure read-only.*
Design produced before its numbers exist gets judged on taste, and taste loses to a panel.

**shape.** [`design-doc`](../../skills/design-doc/SKILL.md) and
[`architecture-diagrams`](../../skills/architecture-diagrams/SKILL.md) together — one artifact
in two renderings. A diagram that disagrees with the doc is a defect in both.

**threat.** [`threat-model`](../../skills/threat-model/SKILL.md) *before* the panel, never
after. It finds that per-API-key limits let one customer's leaked key exhaust the org quota.
Back to `shape` — and note this cost you nothing, because no code exists yet.

**G1 — review panel.** [`council-review`](../../skills/council-review/SKILL.md) seats the
standing panel, takes positions *before* cross-talk, and records dissent. Verdict:
`PROCEED WITH CONDITIONS` — ship it, but the operator seat wants the limiter's failure mode
documented before launch.

**What G1 refuses:** a design nobody attacked, and consensus that was never tested. Treating
`PROCEED WITH CONDITIONS` as `PROCEED` is the most common failure here — the condition is
part of the decision and must reach the ADR.

**record last.** [`adr-generator`](../../skills/adr-generator/SKILL.md) — *after* it is a
decision, carrying the condition and the rejected options. An ADR written before G1 is a
proposal in an ADR's clothes.

---

## Loop 3 — `build`

### `shape` → `implement` → **G2 (mechanical)** → `decide` → **G2.1 (human)**

**shape.** [`user-story-splitter`](../../skills/user-story-splitter/SKILL.md) turns the ADR
into vertical slices with criteria a test can assert. "Rate limiting works" is not a slice;
*"a key over its plan limit gets 429 with Retry-After"* is.

**implement.** [`feature-implement-loop`](../../skills/feature-implement-loop/SKILL.md) runs
its own capped generate-challenge cycle inside this stage.

**G2 — mechanical.** [`pre-merge-review`](../../skills/pre-merge-review/SKILL.md) runs
`gate.py`. **The exit code is the verdict.** Round 1: `NOT READY` — no test for the Redis-down
path, which the NFR explicitly required. Back to `implement`. Round 2: `READY`.

**What G2 refuses:** an argument. You cannot reason a red gate green, and editing the gate or
the test to make it pass converts a mechanical gate into a decorative one. The cap is 3 — on
a third `NOT READY`, stop and emit `BLOCKED` naming what did not converge. A fourth round is
a defect in the loop, not diligence.

**G2.1 — human.** A person merges. Design disagreements surfaced at G2 escalate to
`council-review` rather than getting argued inside the diff.

---

## Loop 4 — `operate`

### `instrument` → `document` → `respond` → **G3 (human)**

**instrument.** [`observability-plan`](../../skills/observability-plan/SKILL.md): alert when
429 rate exceeds 5% for any single key over 10 minutes. You cannot respond to what you never
detected.

**document.** [`runbook-generator`](../../skills/runbook-generator/SKILL.md) writes the
procedure for that alert. An alert with no procedure wakes someone who then has to think.

**respond.** Two weeks later the alert fires — a customer's retry loop is hammering the API.
[`incident-comms`](../../skills/incident-comms/SKILL.md), staged: *detect*, *mitigate*,
*resolve* have different audiences and different truths.

**G3 — human, and the feedback edge that matters.**
[`postmortem-generator`](../../skills/postmortem-generator/SKILL.md) is blameless and ends in
**runbook deltas**. The finding: the runbook said "raise the limit," which treats the symptom.
`REVISE` sends those deltas back to `document`, and the loop closes.

**What G3 refuses:** a postmortem that changes no procedure — that is a story about an outage.
And never guess the numbers to finish one; state the gap, because a postmortem's entire value
is its accuracy.

---

## What you just saw

| Gate | Kind | Refused |
|---|---|---|
| **G0** | human | a brief with `[missing]` fields nobody filled |
| **G1** | review | a design nobody attacked; untested consensus |
| **G2** | mechanical | an argument — the exit code decides |
| **G3** | human | a postmortem that changed no procedure |

Four gates, four different kinds, chosen by **how expensive the mistake is to unwind** — a
re-brief, months of code, a revert, live users. That is the whole model.

Every skill above also runs standalone. You can invoke
[`adr-generator`](../../skills/adr-generator/SKILL.md) on its own and never touch a loop;
the loop is what supplies the order and the gates between them.

Next: [Why loops](../explanation/loops.md) for the reasoning, or
[Author a new loop](../how-to/author-a-loop.md) to build your own.

---
title: Follow one change through the loops
summary: A single realistic change — API rate limiting — walked from a stakeholder complaint to a closed incident, showing what each stage produces and what each gate actually refuses.
kind: tutorial
---

# Follow one change through the loops

One change, four stages, start to finish. The point is not the artifacts — it is seeing
**what each gate refuses**, because a gate that never refuses anything is decoration. Two of
the stages run as loops (`design`, `build`). Finding the problem and running the service run
as skills in order: their loops were retired, because on held-out evals the same skills used
without the loop were preferred.

Install what you need as you go, or take it all up front:

```bash
npx skilldrop-cli install --loop design build
npx skilldrop-cli install --pack product-manager
npx skilldrop-cli install --pack sre-oncall
```

The change: *"Enterprise customers keep hitting our API limits and complaining."*

---

## Find the problem worth solving

### `requirements-interview` → `brief-intake` → `prd-draft` → **you agree it**

**gather.** The signal arrived as a complaint from an account manager, so this is a
conversation, not a journey map. Run [`requirements-interview`](../../packs/product-manager/skills/requirements-interview/SKILL.md).
It comes back with the thing that matters: nobody has said *which* limit, *which* customers,
or what "keep hitting" means numerically.

**structure.** Run [`brief-intake`](../../packs/core/skills/brief-intake/SKILL.md). Every field gets a tag:

```
Problem     [explicit]  "Enterprise customers hit API limits" — AM, Slack, 12 Sep
Scope       [inferred]  the public REST API — nobody said so
Threshold   [missing]   no current limit documented
Impact      [missing]   how many customers, how often
```

> 🚩 **Missing for downstream:** `prd-draft` will refuse to write requirements without
> a measured threshold and an affected-customer count.

**This is the order doing its job.** Two `[missing]` tags are worth more than a confident PRD
built on a guess. Go get the numbers: 3 customers, ~40 rejections/day, current limit 100 req/min.

**specify.** Run [`prd-draft`](../../packs/product-manager/skills/prd-draft/SKILL.md) on the now-complete brief.

**You agree it.** A person agrees that *tiered limits per plan* is the problem worth
solving. No script can tell you that you solved the wrong problem well, so this decision is
yours, not a gate's.

**What you refuse:** a brief with `[missing]` fields nobody filled. If your stakeholder says
*"actually, they want burst capacity, not a higher ceiling"*, start again from the
interview: re-briefing cannot fix a wrong problem.

---

## Loop 1 — `design`

### `constrain` → `shape` → `threat` → **G1 (review)** → `record`

**constrain first, always.** [`nfr-spec`](../../packs/solution-architect/skills/nfr-spec/SKILL.md) before any
structure: *limit decisions add ≤5ms p99; the limiter survives a Redis failure read-only.*
Design produced before its numbers exist gets judged on taste, and taste loses to a panel.

**shape.** [`design-doc`](../../packs/solution-architect/skills/design-doc/SKILL.md) and
[`architecture-diagrams`](../../packs/solution-architect/skills/architecture-diagrams/SKILL.md) together — one artifact
in two renderings. A diagram that disagrees with the doc is a defect in both.

**threat.** [`threat-model`](../../packs/solution-architect/skills/threat-model/SKILL.md) *before* the panel, never
after. It finds that per-API-key limits let one customer's leaked key exhaust the org quota.
Back to `shape` — and note this cost you nothing, because no code exists yet.

**G1 — review panel.** [`council-review`](../../packs/core/skills/council-review/SKILL.md) seats the
standing panel, takes positions *before* cross-talk, and records dissent. Verdict:
`PROCEED WITH CONDITIONS` — ship it, but the operator seat wants the limiter's failure mode
documented before launch.

**What G1 refuses:** a design nobody attacked, and consensus that was never tested. Treating
`PROCEED WITH CONDITIONS` as `PROCEED` is the most common failure here — the condition is
part of the decision and must reach the ADR.

**record last.** [`adr-generator`](../../packs/solution-architect/skills/adr-generator/SKILL.md) — *after* it is a
decision, carrying the condition and the rejected options. An ADR written before G1 is a
proposal in an ADR's clothes.

---

## Loop 2 — `build`

### `shape` → `implement` → **G2 (mechanical)** → `decide` → **G2.1 (human)**

**shape.** [`user-story-splitter`](../../packs/dev-team/skills/user-story-splitter/SKILL.md) turns the ADR
into vertical slices with criteria a test can assert. "Rate limiting works" is not a slice;
*"a key over its plan limit gets 429 with Retry-After"* is.

**implement.** [`feature-implement-loop`](../../packs/dev-team/skills/feature-implement-loop/SKILL.md) runs
its own capped generate-challenge cycle inside this stage.

**G2 — mechanical.** [`pre-merge-review`](../../packs/dev-team/skills/pre-merge-review/SKILL.md) runs
`gate.py`. **The exit code is the verdict.** Round 1: `NOT READY` — no test for the Redis-down
path, which the NFR explicitly required. Back to `implement`. Round 2: `READY`.

**What G2 refuses:** an argument. You cannot reason a red gate green, and editing the gate or
the test to make it pass converts a mechanical gate into a decorative one. The cap is 3 — on
a third `NOT READY`, stop and emit `BLOCKED` naming what did not converge. A fourth round is
a defect in the loop, not diligence.

**G2.1 — human.** A person merges. Design disagreements surfaced at G2 escalate to
`council-review` rather than getting argued inside the diff.

---

## Run it

### `observability-plan` → `runbook-generator` → `incident-comms` → `postmortem-generator`

**instrument.** [`observability-plan`](../../packs/sre-oncall/skills/observability-plan/SKILL.md): alert when
429 rate exceeds 5% for any single key over 10 minutes. You cannot respond to what you never
detected.

**document.** [`runbook-generator`](../../packs/sre-oncall/skills/runbook-generator/SKILL.md) writes the
procedure for that alert. An alert with no procedure wakes someone who then has to think.

**respond.** Two weeks later the alert fires — a customer's retry loop is hammering the API.
[`incident-comms`](../../packs/sre-oncall/skills/incident-comms/SKILL.md), staged: *detect*, *mitigate*,
*resolve* have different audiences and different truths.

**learn, and the feedback edge that matters.**
[`postmortem-generator`](../../packs/sre-oncall/skills/postmortem-generator/SKILL.md) is blameless and ends in
**runbook deltas**. The finding: the runbook said "raise the limit," which treats the symptom.
Feed those deltas back to `runbook-generator`, and only then close the incident.

**What you refuse:** a postmortem that changes no procedure — that is a story about an outage.
And never guess the numbers to finish one; state the gap, because a postmortem's entire value
is its accuracy.

---

## What you just saw

| Where | Who decides | Refused |
|---|---|---|
| Finding the problem | you | a brief with `[missing]` fields nobody filled |
| **G1** | review panel | a design nobody attacked; untested consensus |
| **G2** | script | an argument — the exit code decides |
| Running it | you | a postmortem that changed no procedure |

Each decision is made by whoever fits **how expensive the mistake is to unwind** — a
re-brief, months of code, a revert, live users. That is the whole model.

Every skill above also runs standalone. You can invoke
[`adr-generator`](../../packs/solution-architect/skills/adr-generator/SKILL.md) on its own and never touch a loop;
the loop is what supplies the order and the gates between them.

Next: [Why loops](../explanation/loops.md) for the reasoning, or
[Author a new loop](../how-to/author-a-loop.md) to build your own.

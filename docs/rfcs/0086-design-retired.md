---
rfc: 0086
title: design retired after a fifth measurement
status: implemented
date: 2026-11-12
author: sanjay-ananth
---

# RFC-0086: design retired after a fifth measurement

## Problem / use case

[RFC-0085](0085-build-retired-design-kept.md) kept `design` 0.5.0. It beat plain Claude Code,
and recorded decisions well. It still lost to its own skills where a repository's rules allow one
decision per ADR, because it bundled several decisions into one record and amended accepted
ADRs.

## Fit check

One loop change, then a retirement in the pattern of RFC-0074 and RFC-0085. No skill, gate or
verdict vocabulary changes. With `design` gone, `release` is the only loop on the lifecycle. The
other four stages are drawn from their skills in order.

## Proposal

**`design` 0.6.0:**
- **One decision per ADR when the house rules say so.** Further decisions go in the design doc as
  decisions still to record, or into their own `Proposed` records when the person asked for
  records.
- **An accepted record changes only for a decision that replaces it.** Otherwise the needed
  change is proposed to its owner.
- **File paths are relative to the working folder.**
- **Every copy of the data that outlives the change is accounted for:** backups, replicas, caches
  and exports.

## Measurement

`design` ran on two fresh held-out evals, written blind from its description:
- a live-tracking design that needs several decisions, under a one-decision-per-record rule;
- a hand-off design where the best answer bends an accepted ADR.

There were two trials on `claude-sonnet-5-5`, judges `claude-sonnet-5-5` and `claude-opus-5-5`,
with `--allow-bash` ([`loops-1.17.0.json`](../benchmarks/loops-1.17.0.json), $4.42).

| `design` 0.6.0 preferred to… (judges 1, 2) | Its own skills | Plain agent |
|---|---|---|
| Both evals | 25%, 25% | 25%, 50% |

Checks met (loop / skills / plain): 91% / 88% / 88%.

- **The live-tracking eval: it lost every pair, to its skills and the plain agent alike.** Both
  of the others wrote one ADR per decision, five in all, numbered and within the page limit. The
  loop wrote a single ADR, bundling the cache, polling and token decisions, and left the rest
  unrecorded. The 0.6.0 rule allowed that: "a decision still to record" in the design doc. So the
  rule written to fix the bundling produced it.
- **The hand-off eval was split.** The loop won with both judges for its separate design doc
  and for catching a second conflict with a retry rule. It lost for superseding only one of the
  two clauses its design broke.

This is `design`'s fifth measurement. Against its skills it was:
1. neither ahead nor behind (RFC-0074);
2. behind (RFC-0083);
3. ahead (RFC-0084);
4. split (RFC-0085);
5. behind, with both judges.

Like `build`, each rebuild traded one failure for another. Its skills, run in order, already do
what the loop's order was meant to add.

## Alternatives considered

- **One more round, with the rule reworded to write each further decision as its own `Proposed`
  ADR.** The loss traces to this round's rule. But a sixth rule fitted to the fifth set of evals
  is the pattern that retired `build`.
- **Revert to 0.5.0 and stop measuring.** 0.5.0 lost the same eval type in round 4, so it would
  ship a known loss with no plan to fix it.

## Decision

Implemented in 1.17.0. **`design` is retired.** Its folder is removed, and a `"kind": "loop"`
record in `catalogue.json` says why and what to run instead:
1. `context-graph` and `nfr-spec`;
2. `design-doc` and `architecture-diagrams`;
3. `threat-model`;
4. `council-review`;
5. `adr-generator`.

The decision stays the person's. The lifecycle's "Decide how to build it" stage is drawn from
those skills, and `release` is the one lifecycle loop left.

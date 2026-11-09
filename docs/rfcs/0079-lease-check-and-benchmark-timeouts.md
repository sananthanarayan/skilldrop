---
rfc: 0079
title: A lease check for startup-legal, and benchmark runs that can't hang
status: implemented
date: 2026-11-09
author: sananthanarayan
---

# RFC-0079: A lease check for startup-legal, and benchmark runs that can't hang

## Problem / use case

A first office lease is often the biggest commitment a young company signs, and founders sign
on the headline rent. The headline hides what matters: the committed cost up to the break, a
three-year index-linked review that compounds at once within its cap, and a break notice date
six months before the break, with conditions that can void it. `startup-legal` (RFC-0078) has
contracts and cap tables; the first lease is the next document a founder signs without a lawyer.

Separately, benchmark runs stalled for hours: when an agent session started a command that
never exits (a network call the sandbox never answers), the harness killed `claude -p` on
timeout but went on waiting for the output pipe the child still held open.

## Fit check

- **Concrete artifact:** a lease's committed costs to each break and the end, every deadline as
  a date, and the clauses to push back on with wording.
- **Portable:** a plain folder; a stdlib Python 3.9+ script that reads only the file it is given
  and contacts no network.
- **Opinionated:** the script decides the dates and sums; the skill leads with the commitment and
  the exits, and names at most two points for a lawyer.
- **Category:** added to `startup-legal` and its outcome. The harness change touches
  `run_bench.py` only.

## Proposal

| Skill | Tier | Script |
|---|---|---|
| `lease-check` | standard | `lease_terms.py`: rent by year through steps and capped, collared, compounded reviews; committed cost to each break (on the lease's own date) and the end; deadlines; contradictions |

`run_bench.py` runs each `claude -p` session in its own process group and kills the whole group
on timeout, so a stuck child can no longer hold a run open; `tests/test_run_bench_timeout.py`
pins it.

## Alternatives considered

- **A general property pack.** The person is still the founder, and the lease is the next
  document after the contracts and the round.
- **Raise the benchmark's time limits.** A hung child never exits, so no limit is long enough.

## Measurement

Two held-out evals written blind from the description (a UK studio's heads of terms, an
Australian lab's heads of agreement); two trials on `claude-sonnet-5-5`; judges
`claude-sonnet-5-5` and `claude-opus-5-5`; `--allow-bash`.

| Skill | Pairs won, judge 1 | Judge 2 | Checks met: skill / plain |
|---|---|---|---|
| `lease-check` | 3 of 4 | 3 of 4 | 89% / 86% |

Both arms got the sums right (£73,200 to the break, £133,200 to the end; A$223,200 and
A$312,998). The skill won on the term ending on 29 February in a leap year, on ranked pushbacks
with wording ready to send, and on the break's strict conditions.

## Decision

Implemented in 1.10.0: `lease-check` in `startup-legal`, and the process-group timeout in
`run_bench.py`.

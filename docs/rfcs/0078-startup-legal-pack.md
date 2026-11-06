---
rfc: 0078
title: A startup legal pack — agreements and cap tables checked by script
status: implemented
date: 2026-11-06
author: sananthanarayan
---

# RFC-0078: A startup legal pack — agreements and cap tables checked by script

## Problem / use case

A founder in the first year signs a customer's MSA, a vendor's order form and three NDAs, and
raises on SAFEs, mostly without a lawyer. Two jobs end in a document whose faults are
mechanical, checkable, and missed by a capable agent asked in plain words:

- **An agreement before signing.** The agent reads it fluently and misses a survival clause
  pointing at a section that was renumbered away, a fee left as `[●]`, "thirty (60) days", an
  exhibit that was never attached, or a renewal notice window that closes in three weeks.
- **A cap table through a round.** Post-money and pre-money SAFEs at different caps, a note
  accruing interest and a pool top-up in the pre-money form a circular calculation. The
  common errors are treating a post-money SAFE as pre-money, converting a note on its
  principal and leaving the pool's cost out of the founders' column.

The catalogue's `grc` pack serves compliance teams; nothing serves a founder with no lawyer.

## Fit check

- **Concrete artifact:** a signing verdict with fixes, faults and dates; an after-round cap
  table with conversion prices.
- **Portable:** plain folders; stdlib Python 3.9+ scripts that read only the file they are
  given, write only a path they are given, and contact no network.
- **Opinionated:** each script decides pass or fail. Each skill reads from the founder's side,
  gives wording rather than advice to "consider", and names at most two points worth a
  lawyer's hour instead of a disclaimer.
- **Category:** a new pack, `startup-legal`, and a new outcome, `handle-the-legal-basics`.

## Proposal

| Skill | Tier | Script |
|---|---|---|
| `contract-check` | heavy | `contract_check.py`: blanks, cross-references to clauses and appendices, numbering, defined terms, words against figures, impossible dates, notice periods and, given the term's end, each renewal notice deadline; .md, .txt and .docx |
| `cap-table` | standard | `cap_table.py`: post- and pre-money SAFEs, notes with simple interest, cap or discount, pool top-up in or after the pre-money, solved together; checks post-money = price × shares and 100 %; scenarios and CSV |

Each carries the rules RFC-0076 and RFC-0077 settled: the reply leads with the answer; no
script, file format, skill name, skill-folder path or temporary path in the reply; the
person's file is never overwritten; working files go in a private `mktemp -d` folder. One rule
is new: **never refuse and never open with a disclaimer; name at most two specific points worth
a lawyer's hour.**

## Alternatives considered

- **Put these in `grc`.** Its audience is a compliance lead with policies and auditors; a
  founder browsing for "contract" or "SAFE" won't look there.
- **A contract-drafting skill.** Drafting from nothing is where an agent's plausible text is
  most dangerous and least checkable. Checking a draft the founder already has is not.
- **Cap tables in `product-manager` or `data-analytics`.** The person is the founder, and the
  document they hold is a legal one (a SAFE, a term sheet).

## Measurement

Two held-out evals each, written blind from the description: two trials on
`claude-sonnet-5-5`, judges `claude-sonnet-5-5` and `claude-opus-5-5`, with `--allow-bash`.

| Skill | Evals | Pairs won, judge 1 | Judge 2 | Checks met: skill / plain |
|---|---|---|---|---|
| `contract-check` | a consulting agreement, a reseller agreement | 3 of 4 | 2 of 4 | 86% / 75% |
| `cap-table` | a seed round, a Series A with two SAFEs and a note | 2 of 4 | 4 of 4 | 79% / 75% |

- **`contract-check`** won on the consulting agreement in all four judgements: ranked fixes,
  wording to paste, and every mechanical fault, including the missing exhibit and the blank
  expense cap. On the reseller agreement both arms found the 1 January 2028 renewal deadline;
  it lost one pair for referring to a check the reader never saw.
- **`cap-table`** reached the same founder percentages as the plain agent (29.17 %, 31.43 %)
  and won where it quantified what moves them: the pool placed after the round, the
  effective pre-money, other valuations. It lost a pair for naming a tool and a scratch path.

Both faults are one rule, now in each skill: never call the work a check or a tool, and never
show a temporary path.

## Decision

Implemented in 1.9.0: `contract-check` and `cap-table` in a new `startup-legal` pack and a
`handle-the-legal-basics` outcome.

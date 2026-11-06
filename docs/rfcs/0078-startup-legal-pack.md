---
rfc: 0078
title: A startup legal pack — agreements, cap tables and privacy policies checked by script
status: accepted
date: 2026-11-06
author: sananthanarayan
---

# RFC-0078: A startup legal pack — agreements, cap tables and privacy policies checked by script

## Problem / use case

A founder in the first year signs a customer's MSA, a vendor's order form and three NDAs,
raises on SAFEs, and publishes a privacy policy from a template, mostly without a lawyer. Three
jobs end in a document whose faults are mechanical, checkable, and missed by a capable agent
asked in plain words:

- **An agreement before signing.** The agent reads it fluently and misses a survival clause
  pointing at a section that was renumbered away, a fee left as `[●]`, "thirty (60) days", an
  exhibit that was never attached, or a renewal notice window that closes in three weeks.
- **A cap table through a round.** Post-money and pre-money SAFEs at different caps, a note
  accruing interest and a pool top-up in the pre-money form a circular calculation. The
  common errors are treating a post-money SAFE as pre-money, converting a note on its
  principal and leaving the pool's cost out of the founders' column.
- **A privacy policy against the product.** The agent reviews the policy's prose. The faults
  are in the code: a Meta pixel beside "we never share your data", an AI API receiving what
  users type, analytics added after the policy was written.

The catalogue's `grc` pack serves compliance teams (DPIAs, SOC 2, questionnaires); nothing
serves a founder with no lawyer.

## Fit check

- **Concrete artifact:** a signing verdict with fixes, faults and dates; an after-round cap
  table with conversion prices; a gap list with paste-ready policy text.
- **Portable:** plain folders; stdlib Python 3.9+ scripts that read only the file or folder
  they are given, write only a path they are given, and contact no network.
- **Opinionated:** each script decides pass or fail. Each skill reads from the founder's side,
  gives wording rather than advice to "consider", and names at most two points worth a
  lawyer's hour instead of a disclaimer.
- **Category:** a new pack, `startup-legal`, and a new outcome, `handle-the-legal-basics`.

## Proposal

| Skill | Tier | Script |
|---|---|---|
| `contract-check` | heavy | `contract_check.py`: blanks, cross-references to clauses and appendices, numbering, defined terms, words against figures, impossible dates, notice periods and, given the term's end, each renewal notice deadline; .md, .txt and .docx |
| `cap-table` | standard | `cap_table.py`: post- and pre-money SAFEs, notes with simple interest, cap or discount, pool top-up in or after the pre-money, solved together; checks post-money = price × shares and 100 %; scenarios and CSV |
| `privacy-policy-check` | standard | `policy_scan.py`: 54 services found from runtime dependencies in nine manifest formats and from script tags and API hosts in source; disclosure by name or kind; claims the code contradicts; missing sections |

Each carries the rules RFC-0076 and RFC-0077 settled: the reply leads with the answer; no
script, file format, skill name or skill-folder path in the reply; the person's file is never
overwritten; working files go in a private `mktemp -d` folder. One rule is new: **never refuse
and never open with a disclaimer; name at most two specific points worth a lawyer's hour.**

**Admission** as RFC-0076: two held-out evals each, written blind from the description; two
trials; judges `claude-sonnet-5-5` and `claude-opus-5-5`; `--allow-bash`. A skill that doesn't
win at least half its pairs with both judges is revised once and measured on fresh blind evals.

## Alternatives considered

- **Put these in `grc`.** Its audience is a compliance lead with policies and auditors; a
  founder browsing for "contract" or "SAFE" won't look there, and `grc`'s skills assume a
  programme a startup doesn't have.
- **A contract-drafting skill.** Drafting from nothing is where an agent's plausible text is
  most dangerous and least checkable. Checking a draft the founder already has is not.
- **Cap tables in `product-manager` or `data-analytics`.** The person is the founder, and the
  document they hold is a legal one (a SAFE, a term sheet).

## Decision

Accepted; admission measurement to follow.

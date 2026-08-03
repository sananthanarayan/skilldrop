---
rfc: 0017
title: Production review panel — a security reviewer and a multi-subagent loop
status: accepted   # draft → accepted | rejected → implemented
date: 2026-08-03
author: sananthanarayan
---

# RFC-0017: Production review panel — a security reviewer and a multi-subagent loop

## Problem / use case

A user asked whether skilldrop has an equivalent to agent-ready-repo's `work-loop` — a supervised
build loop that drives **multiple** cold-read reviewer subagents to get code to production grade.
skilldrop has the loop (`feature-implement-loop`) and two reviewer subagents (`devils-advocate` =
correctness, `code-quality` = craft), but two gaps vs. that model:

1. **No security reviewer subagent.** Security is one bullet inside `devils-advocate`'s
   staff-engineer lens, and `threat-model` is a *design*-phase skill (STRIDE over a design, before
   code) — neither is a focused **code-diff** security review. agent-ready-repo's `work-loop` runs a
   distinct security reviewer alongside its adversarial and quality reviewers.
2. **The loop drives only one reviewer.** `feature-implement-loop`'s review step delegated to
   `devils-advocate` alone; craft and security were left to the human to invoke à la carte.

Designed with skilldrop's own `subagent-design` (context isolation, one mission per agent,
verification-never-a-generator) and `agent-loop-design` (generate→verify→gate, hard cap, human gate)
skills. The design conclusion was **not** a new orchestrator skill — that would duplicate
`feature-implement-loop` (AGENTS.md: improve the existing one, don't duplicate). It is: add the
missing reviewer, and upgrade the existing loop to drive the full panel.

## Fit check (structural change)

- **Golden rules:** no skill moves; `feature-implement-loop` is *improved*, not replaced (so no
  new-skill RFC would even be required for that half — this RFC exists for the new agent + to record
  the design decision). `security-reviewer` is a new file under the existing `agents/` primitive
  (RFC-0012), not a new top-level directory.
- **"Split, not merged" (agents/README):** the new reviewer *extends* that principle — three lenses
  (correctness · security · craft), each a separate pass, rather than one diluted "review my code"
  agent. It does not merge into `devils-advocate`.
- **Not duplicative:** `security-reviewer` reviews a **diff for exploitability**; `threat-model`
  models a **design's** threat surface; `devils-advocate` hunts **general** bugs. The boundary is
  stated in each agent's body.
- **Portability:** the loop still runs everywhere — subagent panel where a tool has subagents, an
  inline lens-sweep (edge cases · assumptions · security · craft) otherwise. No harness dependency.

## Proposal

1. **New agent `agents/security-reviewer.md`** — application-security reviewer of a change: authz/IDOR,
   injection (source→sink), secret exposure, SSRF, unsafe deserialization, path traversal, weak
   crypto, risky new deps. Severity-tagged findings with `file:line`, a one-line attacker scenario,
   and a concrete control; each marked confirmed vs. needs-verification. Read-and-reason only, never
   active exploitation; explicitly not a full audit / SAST substitute / human sign-off.
2. **`feature-implement-loop` step 4 → a review panel.** Where subagents exist, delegate the diff in
   **parallel** to `devils-advocate` + `security-reviewer` + `code-quality`, each in a fresh context;
   elsewhere sweep the lenses inline. Acceptance-criteria→asserting-test coverage stays the loop
   driver's own job (the reviewers check code; the loop owns the contract). Findings are merged and
   de-duped before the unchanged gate (blocker/major/uncovered-criterion → another round; 3-round
   cap; honest report).
3. **Docs:** `agents/README` gains the third reviewer and reframes the panel; the README
   `feature-implement-loop` row reflects the panel.

Anti-patterns this bans: a new duplicate "work-loop" skill; a merged review-everything agent; a loop
that self-certifies past a toothless single-reviewer round.

## Alternatives considered

- **A new `production-review-loop` skill** that orchestrates the panel. Rejected — it duplicates
  `feature-implement-loop`'s generate→verify→gate cycle; the honest move is to upgrade that loop.
- **Fold security into `devils-advocate`.** Rejected — violates "split, not merged"; a security lens
  and an edge-case lens pull in different directions and dilute each other (the same reason craft is
  already separate).
- **Reuse `threat-model` for the code pass.** Rejected — it's design-phase STRIDE, not a diff review;
  wrong altitude and wrong input.
- **Add an implementer subagent** (as work-loop has). Deferred — skilldrop's loop generates directly;
  a separate implementer buys little without a harness enforcing fresh-context isolation, and adds
  orchestration cost. Revisit if a generation-isolation need appears.

## Decision

Accepted and implemented: `agents/security-reviewer.md` added; `feature-implement-loop` drives the
three-reviewer panel in parallel with an inline fallback; docs updated. skilldrop now ships a
multi-subagent production-grade review loop — the loop, the three-lens reviewer panel, and (for the
harder calls) `council-review` — assembled from portable primitives rather than a single harness.

---
rfc: 0025
title: Output hygiene
status: implemented   # draft → accepted | rejected → implemented
date: 2026-09-18
author: sananthanarayan
---

# RFC-0025: Output hygiene

## Problem / use case

A knowledge worker pastes an agent-written exec summary into a board deck, or lands an
agent-written commit, and ships three things they never chose: harness-added provenance
(`Co-Authored-By: Claude`, the `🤖 Generated with Claude Code` PR footer — 104 of this
repo's first 123 commits carry one), chat-paste artifacts (non-breaking spaces, narrow
no-break spaces, zero-width joiners, curly quotes that break a plain-text pipeline), and
prose tells (the closing "Let me know if you'd like me to expand any section", the
"it's not just X, it's Y" cadence, the bolded lead-in on every bullet). The first two are
mechanical and a script should catch them. The third is judgment and needs a model pass.
Today the user finds these one at a time, in the wrong place, after sending.

There is no cryptographic watermark in Claude's text output to remove, and this skill does
not claim to defeat one. It cleans artifacts of the transport and the drafting style —
which is why it is named for hygiene and not for watermarks.

## Fit check

- **Concrete artifact:** a findings report (severity-tagged, each finding quoting the exact
  offending span with its Unicode codepoint or matched line) plus, on request, the cleaned text.
- **Portable:** plain folder copy; `scripts/scrub.py` is stdlib-only Python 3 and reads a path
  or stdin, so it runs identically under Claude Code, Cursor, Kiro, Codex, and bare `python3`.
- **Opinionated:** it decides which classes are auto-fixable (invisible characters, spacing
  characters, provenance trailers, trailing chat closers) and which are report-only because a
  blind rewrite would corrupt meaning (homoglyphs, typographic punctuation in Markdown). It
  refuses to strip provenance where disclosure is owed, rather than asking.
- **Category:** Pipeline glue — it acts on other skills' outputs, alongside `brief-intake`
  (upstream) and `doc-critique` (substance).

## Proposal

- `name`: `output-hygiene`. Tier **standard** — the mechanical pass is a script, so the model
  is doing bounded rewriting of flagged prose against a fixed tell list, not adversarial review.
- `related`: `doc-critique` (hand-off when the problem is the argument, not the surface),
  `ai-usage-policy` (the counterweight — it defines where disclosure is mandatory).
- Quality bar sketch: every finding names a codepoint or quotes the matched line, so the user
  can verify it rather than trust it; the report separates auto-fixable from judgment classes
  and never silently applies the second; a de-telled rewrite changes cadence only, never a
  claim, number, or hedge that was carrying meaning.
- Banned anti-patterns: (1) reporting "this reads like AI" without quoting the span that does;
  (2) laundering authorship — stripping provenance from a submission where an academic,
  employer, journal, or contribution policy requires disclosure. The skill names the four
  contexts where it stops and says so instead of cleaning.

Ships `scripts/scrub.py` (report by default, `--fix` to write, `--json` for hooks, non-zero
exit on findings so it can gate a commit) and `reference.md` (the full tell taxonomy with a
passing and failing example per tell).

## Alternatives considered

- **Extend `doc-critique`.** Lost: that skill reviews whether a document made its case, against
  per-archetype rubrics. Surface hygiene applies to commits, chat replies, and code comments
  that have no archetype and no argument. Merging them would blunt both.
- **Ship the script alone, no skill.** Lost: the script cannot catch the prose tells, which are
  the half the user actually can't see.
- **Do nothing.** Lost: the artifacts are shipping today, and the provenance trailer specifically
  is a per-repo decision that a settings toggle handles prospectively but nothing handles for
  text pasted out of a chat window.

## Decision

Accepted 2026-09-18 and implemented in the same change: skill, script, reference, evals,
`packs.json` membership (`stakeholder-comms`, `dev-team`), `model-routing.json` entry.

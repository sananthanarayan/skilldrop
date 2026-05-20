---
name: doc-critique
description: Review an existing document — ADR, design doc, runbook, exec summary, tech-comparison matrix, deck outline, decision log — and produce a structured critique against the same quality bars the skilldrop generators enforce. Categorizes findings by severity (blocker / major / minor / nit), points to the exact section/line, and suggests a concrete fix for each. Use when the user wants a second-pair-of-eyes review before sharing a doc, or has been handed someone else's artifact and wants to know what to push back on.
---

# doc-critique

You help the user review an existing document with the same opinionated rubric the skilldrop generators use to *produce* them. The collection is otherwise asymmetric — every other skill creates artifacts; this one reviews them.

## How to respond

1. **Identify the doc type.** Ask if the user hasn't said. Match it to the closest skilldrop archetype:

   | Doc type | Rubric file |
   |---|---|
   | ADR (MADR or Nygard) | [`rubrics/adr.md`](rubrics/adr.md) |
   | Engineering design doc / RFC / tech proposal | [`rubrics/design-doc.md`](rubrics/design-doc.md) |
   | Runbook / operational doc | [`rubrics/runbook.md`](rubrics/runbook.md) |
   | Tech-comparison matrix / vendor selection | [`rubrics/tech-comparison.md`](rubrics/tech-comparison.md) |
   | Exec summary / 1-pager | [`rubrics/exec-summary.md`](rubrics/exec-summary.md) |
   | Slide deck or outline | [`rubrics/deck.md`](rubrics/deck.md) |
   | Decision log / meeting notes | [`rubrics/decision-log.md`](rubrics/decision-log.md) |
   | _Other / unsure_ | Use `rubrics/generic.md` and call out the type-mismatch |

   For mixed/ambiguous docs (e.g. "a design doc that's also being used as a runbook"), pick the *primary* purpose and note the dual-use in the critique header.

2. **Read the whole doc before commenting.** A finding that looks like a blocker on page 1 sometimes gets resolved by page 4 — don't fire critique at sections in isolation.

3. **Apply the rubric, not your taste.** Each rubric has a fixed set of checks. Walk through them in order. If a check passes, note it pass-by-default (don't flood the output with green checkmarks); if it fails, write a finding.

4. **Categorize every finding by severity:**

   | Severity | Meaning |
   |---|---|
   | 🟥 **Blocker** | The doc can't ship without fixing this. A reviewer/exec/on-caller will be unable to act on the doc as-is. Example: ADR with no alternatives considered; runbook with no rollback command; exec summary missing The Ask. |
   | 🟧 **Major** | The doc will ship and be used but a key decision is poorly supported / a section is missing or weak / a claim is unsupported. The doc loses credibility but doesn't fail outright. |
   | 🟨 **Minor** | Style, ordering, redundancy, missing nice-to-haves. The doc works; this is the difference between "passable" and "good". |
   | ⚪ **Nit** | Typo, formatting, terminology preference. Optional. |

   When in doubt between two severities, downgrade. Inflated severity makes the critique unreadable.

5. **For every finding, write three lines:**

   - **Where:** quote 5–10 words verbatim from the doc, or cite the section heading + paragraph (e.g. *"§ Risks, ¶2"*). The user must be able to jump to the exact spot.
   - **What's wrong:** name the failing rubric check in one sentence.
   - **Suggested fix:** concrete. ✅ "Add a 'why-not' to the DynamoDB option (one sentence — likely 'cross-table transactions not supported')." — ❌ "Improve the alternatives section."

6. **Open with a verdict, not a critique.** The first thing the user reads is a one-line verdict + a 3-sentence executive summary:

   ```
   Verdict: SHIP WITH CHANGES — 1 blocker, 4 major, 6 minor.

   The decision and trade-offs are clear, but two of the four "considered options" are described without a why-not, which breaks the ADR's audit value. The status field is set to "Accepted" but no deciders are listed, which the team's ADR policy requires. Minor issues are mostly tone (hedging language) and one out-of-order section.
   ```

   Verdicts are one of: `SHIP IT`, `SHIP WITH CHANGES`, `MAJOR REWRITE`, `WRONG ARTIFACT`. The last one is for when the doc is the wrong *kind* — e.g. user wrote a design doc but the situation needs an ADR.

7. **Output structure** — use [`templates/critique.md`](templates/critique.md):

   ```markdown
   # Critique: {doc title}
   _Type: {ADR | design-doc | …} · Reviewed: {YYYY-MM-DD} · Rubric: {rubric file}_

   ## Verdict
   {one-liner} — {N} blocker, {N} major, {N} minor, {N} nit
   {3-sentence summary}

   ## Findings

   ### 🟥 Blockers
   1. **Where:** *"…"* (§ Section, ¶N)
      **What:** {one sentence}
      **Fix:** {one sentence, concrete}

   ### 🟧 Major
   …

   ### 🟨 Minor
   …

   ### ⚪ Nits
   …

   ## What's working
   - {2–4 specific things the doc does well — not flattery, real reusable strengths}
   ```

8. **End with "what's working"**, not more criticism. Two reasons: (a) the user often wants to know which parts to *keep* during a rewrite, and (b) finishing on weak points trains the user to dread review rather than ask for it.

## Quality bar

- **Severity is calibrated.** If your output has more blockers than major issues, you're inflating. Reread and demote.
- **Findings are local, not global.** "The whole tone is off" is not a finding; "§ TL;DR uses 'innovative' and 'leverage' — replace with concrete verbs" is.
- **Fixes are paste-able where possible.** If the fix is "add an X section", show what the X section should contain in 2–3 bullets.
- **Don't review the topic, review the doc.** It's not your job to redebate whether Postgres beats DynamoDB — only whether the doc made its case competently.
- **Quote the doc, don't paraphrase.** Just like `decision-log`, the quoted snippet is the audit trail that proves you read the actual words.

## When to use this skill

- ✅ Before publishing an ADR, design doc, or runbook — author wants a sanity check.
- ✅ When the user is asked to review someone else's doc and wants a structured frame.
- ✅ As a checkpoint after one of the generator skills, before the user shares the artifact externally.
- ✅ When the user says "is this any good?" with a doc attached.

## When NOT to use this skill

- ❌ For evaluating the *underlying decision* (is Postgres the right choice?). That's a tech-debate, not a doc review — use `tech-comparison-matrix` instead.
- ❌ For grammar / spelling pass on a doc that's otherwise solid. Use a normal editor.
- ❌ For evaluating code. This skill reviews *documents*; for code review, the user has other tools.
- ❌ For generating the doc. If the user wants a draft, that's the matching generator skill.

## Anti-patterns to avoid

- ❌ Severity inflation. If everything is a blocker, nothing is.
- ❌ Vague findings ("clarify the proposal section"). Always quote and always suggest a fix.
- ❌ Critiquing the *author's voice* — comment on the doc's *fitness for purpose*, not personality.
- ❌ Restating the rubric ("ADRs should have alternatives"). The finding is about *this* doc's failure to meet it.
- ❌ Skipping "What's working." The user came for honesty in both directions.
- ❌ Re-debating the underlying decision. The doc could make a great case for the wrong choice — and that's still a "ship it" from the doc's perspective.

---
name: hypothesis-comparison
description: Compare rival explanations for an observation with analysis of competing hypotheses (ACH) — list the hypotheses and the evidence, build a consistency matrix (consistent / inconsistent / neutral), rank hypotheses by how little evidence contradicts them rather than how much supports them, name the diagnostic evidence and the linchpins, and say which next observation would tell the leaders apart. Use when the user asks "why did X happen", "which explanation fits the evidence", "what's really causing this", wants to stop arguing over a favourite theory, or says "compare these hypotheses", "competing explanations", "ACH".
---

# hypothesis-comparison

You help the user decide between rival explanations without falling for the first one that
fits. The method is analysis of competing hypotheses (ACH), described by Richards Heuer in
*Psychology of Intelligence Analysis*: put every hypothesis against every piece of evidence,
and keep the hypothesis with the **least evidence against it**. Evidence that fits every
hypothesis feels persuasive and proves nothing, so the matrix makes that visible. The output
is a ranked matrix, the evidence the ranking rests on, and the next observation to make.

This skill explains a past or current observation. To choose between options going forward,
use `tech-comparison-matrix` (technology) or `strategy-analysis` (market position). To gather
the evidence in the first place, plan it with `research-plan` and summarise sources with
`source-synthesis`.

## How to respond

**Four rules come before the steps and outrank them:**

- **Answer what was asked, first.** Open with the answer, the decision or the artifact, in plain words. Scores, matrices, frameworks and tags come after it, and anything that doesn't change the answer is cut.
- **Use only what you were given.** Don't add facts, names, numbers, incidents, history, steps or sections the input doesn't contain. What you need and don't have is left out of the artifact and listed once at the end under "To confirm".
- **Deliver from what you have.** When the request gives you something to work on, state your assumptions in a line and produce the result. When it gives you nothing to work on, ask for it in one or two plain sentences and say what you will do once you have it.
- **Write for someone who has never heard of this skill.** No skill names, no paths or scripts from this folder, no internal terms, and nothing about how the run was set up. A next step is one plain sentence at the end that describes the work.
- **For this skill:** End on the hypothesis the evidence favours, with your confidence, when one is ahead; a tie is for when the evidence really is even. Check shares against absolute numbers before scoring: a stable share of a larger total is a rise.

1. **Ask once for what's missing.** You need three things: the **observation** to explain,
   stated as a fact with a time and a size (✅ *"Mobile conversion fell 18% from 8 Sep"* — ❌
   *"sales are weird"*); the **evidence** the user has; and any **hypotheses** already on the
   table. Ask for all missing ones in one message, at most two questions. If the user gives a
   synthesis from `source-synthesis`, take its findings as the evidence list, with citations.

2. **Write at least four hypotheses, and make them rivals.** Include the user's favourite,
   the obvious alternative, a "nothing changed, it's measurement" hypothesis (tracking,
   definitions, sampling), and a "chance or normal variation" hypothesis where the numbers
   allow it. Each hypothesis is one sentence that could be false. If two hypotheses predict
   the same thing for every piece of evidence, merge them. If they overlap, say how the
   matrix treats them (for example "H1 and H2 can both be true; rated as if each acts alone").

3. **List the evidence as observations, not conclusions.** One row per item, each with its
   source. Include **absences**: something that should have happened under a hypothesis and
   didn't is often the most diagnostic row. Add assumptions that carry weight as rows too,
   marked `[assumption]`. Give each row a weight from 0.5 to 2 for credibility and relevance;
   a rumour is 0.5, a primary record is 2. Say why for anything not 1.

4. **Fill the matrix one row at a time, across all hypotheses.** For each piece of evidence,
   ask: "if this hypothesis were true, how likely is this observation?" Rate it `CC` (very
   consistent), `C`, `N` (neutral), `I` (inconsistent), `II` (very inconsistent) or `NA`.
   Work across a row, not down a column, so you judge the evidence and not your favourite
   hypothesis. Rules in [`reference.md`](reference.md).

5. **Score it.** Save the matrix as a CSV in the shape of
   [`templates/matrix.csv`](templates/matrix.csv) and run:

   ```bash
   # Claude Code
   python3 "${CLAUDE_SKILL_DIR}/scripts/ach_matrix.py" matrix.csv -o ach-report.md
   # Other IDEs (from the skill folder)
   python3 scripts/ach_matrix.py matrix.csv -o ach-report.md
   ```

   The script ranks by weighted inconsistency (`I` = 1 × weight, `II` = 2 × weight, the rest
   0), marks non-diagnostic rows, and drops each row in turn to find the **linchpins** whose
   removal changes first place. If no script can run, do the same three steps by hand and
   show the arithmetic.

6. **Read the result, don't just report it.**
   - **Rank by inconsistency.** The leader is the hypothesis hardest to rule out, not the one
     with the most `C` ratings. Say so when the two differ.
   - **Name the diagnostic evidence**: the rows rated differently across the leading
     hypotheses. Name the non-diagnostic rows too, and stop citing them as support.
   - **Check the linchpins.** For each one, say where it came from and what would happen if it
     were wrong or misread. A ranking that rests on one weak row is a lead, not a conclusion.
   - **Say what kills each survivor:** the observation that would move each top hypothesis to
     `I` or `II`.

7. **Name the next observation that discriminates.** Pick the cheapest check that the top two
   hypotheses predict differently, and write it as a test: what to look at, what result
   supports which hypothesis, who can get it, and how long it takes. ✅ *"Pull iOS Safari
   checkout errors from the payment SDK logs for 7–9 Sep. H1 predicts a spike after 22:00 on
   the 7th; H4 predicts none."*

8. **Write it up with [`templates/hypothesis-comparison.md`](templates/hypothesis-comparison.md)**:
   the observation, hypotheses, the matrix, the ranking with scores, diagnostic and
   non-diagnostic evidence, linchpins, the conclusion with a confidence word and why, and the
   next observation. Keep the conclusion tentative where the evidence is thin, and say how
   thin.

**Non-interactive runs** (subagent, CI, headless): a missing observation emits
`BLOCKED: need the observation to explain, with its time and size`. Missing hypotheses are
generated per step 2 and tagged `[assumption]`. If the user supplied no evidence at all, emit
`BLOCKED: need the evidence to rate`, because a matrix of invented evidence ranks nothing.

## Useful references in this skill

- [`reference.md`](reference.md) — the ACH steps, how to rate a cell, weighting, diagnosticity, the usual failure modes, and when ACH is the wrong tool
- [`templates/matrix.csv`](templates/matrix.csv) — the CSV the script reads
- [`templates/hypothesis-comparison.md`](templates/hypothesis-comparison.md) — the write-up skeleton
- [`scripts/ach_matrix.py`](scripts/ach_matrix.py) — scores the matrix, flags non-diagnostic rows, finds linchpins (stdlib only)
- [`examples/conversion-drop.md`](examples/conversion-drop.md) — worked example: a checkout conversion drop, four hypotheses, nine pieces of evidence, real script output

## Quality bar

- **At least four rival hypotheses,** including a measurement one, each a sentence that could be false.
- **Evidence rows are observations with a source,** including at least one absence where one exists. Nothing in the matrix is evidence the user didn't supply, except rows tagged `[assumption]`.
- **The ranking is by inconsistency.** The write-up never argues for a hypothesis by counting its `C` ratings.
- **Non-diagnostic evidence is named and set aside,** not used as support.
- **Linchpins are named and checked:** the rows whose removal changes the leader, with where each came from.
- **The conclusion carries a confidence word and a reason,** and stays tentative when one row holds it up.
- **The next observation discriminates between the top two,** with the result each one predicts.

## When to use this skill

- ✅ "Why did conversion / churn / latency / incident rate change?" with several plausible causes
- ✅ A team stuck arguing for favourite explanations, and needing a neutral way to rank them
- ✅ Making sense of a finished `source-synthesis` when the sources point to different explanations
- ✅ Deciding what to investigate next when you can't check everything

## When NOT to use this skill

- ❌ Choosing between technologies, vendors or approaches for the future — `tech-comparison-matrix`
- ❌ Market or competitive position, SWOT, Five Forces — `strategy-analysis`
- ❌ Planning what evidence to collect before you have any — `research-plan`
- ❌ Summarising what a set of sources says — `source-synthesis`
- ❌ Reviewing someone's written argument for weak spots — `doc-critique`
- ❌ Writing up an incident's timeline and causes once they're known — `postmortem-generator`

## Anti-patterns to avoid

- ❌ **Counting support.** "H1 is consistent with 7 of 9 items" says little if those items fit every hypothesis.
- ❌ **Two hypotheses, one of them a straw man.** Rivals have to be plausible enough to lose to.
- ❌ **Leaving out "it's the measurement".** Tracking changes, new definitions and sampling explain more drops than anyone expects.
- ❌ **Filling the matrix column by column.** You end up rating evidence by how well it fits your favourite.
- ❌ **Evidence that is really a conclusion,** like "the release was buggy". Write what was observed.
- ❌ **A confident verdict resting on one linchpin** nobody has checked.
- ❌ **"More research needed"** as the next step. Name the one observation and what each result means.

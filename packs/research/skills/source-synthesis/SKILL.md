---
name: source-synthesis
description: Synthesise a set of supplied sources — papers, articles, reports, interview transcripts — into findings where every claim is cited to a source and a location ([S1:p4]), agreement and disagreement across sources are explicit, each finding carries an evidence-strength rating with the criteria used, and the gaps and what the sources do not say are listed. Never adds outside facts unless tagged as such, and ships a citation checker. Use when the user hands over several sources and asks to "synthesise these", "what do these papers say", "literature review", "pull the findings together", or "where do the sources agree and disagree".
---

# source-synthesis

You turn a pile of sources the user supplied into findings they can rely on and check. Every
claim points to a source and a place in it, so a reader can verify it in under a minute.
Where sources agree, you say how many and which; where they disagree, you show both sides and
why they might differ. You add nothing from your own knowledge unless it is tagged
`[outside]`. The synthesis is only as good as its sources, so each finding says how strong its
evidence is and on what criteria.

What to research and where to look comes first, from `research-plan`. If the findings point to
several rival explanations, rank them with `hypothesis-comparison`. To turn messy material into
a brief for another skill rather than findings, use `brief-intake`.

## How to respond

1. **Ask once for what's missing.** You need the **sources** themselves (text, files or
   excerpts, not titles) and the **question** the synthesis answers. If the user has a
   research plan, take the question and sub-questions from it. Ask for both in one message.
   If the user sends only titles or links you can't open, ask for the text. Don't summarise a
   paper from memory.

2. **Register the sources.** Give each one an id (`S1`, `S2`, …) and one line: author or owner,
   title, date, type (peer-reviewed study, survey, internal report, news article, interview,
   opinion piece), and for studies the method and sample size if the source states them. Note
   how location works in each: page numbers, section numbers, or timestamps for transcripts.
   Mark sources that aren't independent (two articles reporting the same survey count as one
   line of evidence).

3. **Extract claims before you synthesise.** For each source, list the claims that bear on the
   question, each with its location, in the source's own terms. Keep the source's hedges:
   "associated with" stays "associated with", not "causes". Quote the key sentence when the
   wording matters.

4. **Group claims into findings, one per sub-question or theme.** For each finding:
   - **State it in one sentence,** worded no stronger than its weakest supporting source.
   - **Cite every source that supports it,** with locations: `[S1:p4; S3:§2.1]`.
   - **Show agreement and disagreement:** "S1, S3 and S4 agree; S2 disagrees", and give the
     likely reason for the disagreement when the sources show one (different population,
     period, definition or method). Don't average conflicting results into a middle answer.
   - **Rate the evidence strength** (strong / moderate / limited / conflicting) and say which
     criteria drove it: independent sources, source type, method, sample size, recency,
     directness. Criteria are in [`reference.md`](reference.md).

5. **List the gaps and what the sources don't say.** Sub-questions no source answers;
   populations, periods or regions no source covers; claims everyone repeats but nobody tests;
   and the question the user is likely to ask next that these sources can't answer. Write
   these as statements: ✅ *"None of the sources measures effects beyond 12 months."*

6. **Tag anything from outside.** If context the sources don't give is genuinely needed (a
   definition, a well-known date), add it with `[outside]` so the reader knows to check it.
   Keep it rare. Never use `[outside]` to fill a gap in the findings; list the gap instead.

7. **Write it up with [`templates/synthesis.md`](templates/synthesis.md):** the question, the
   source register, the bottom line in three sentences or fewer, findings with citations and
   strength, the agreement and disagreement table, gaps, what the sources do not say, and the
   `[outside]` list.

8. **Check every citation.** Save the draft and run:

   ```bash
   # Claude Code
   python3 "${CLAUDE_SKILL_DIR}/scripts/citations.py" synthesis.md -o citation-check.md
   # Other IDEs (from the skill folder)
   python3 scripts/citations.py synthesis.md -o citation-check.md
   ```

   It reads the `## Sources` section of the draft (or a separate file with `--sources`), and
   reports citations that don't resolve, malformed citations, paragraphs and table rows with no
   citation, citations with no location, sources never cited, and every `[outside]` claim. Fix
   every error, and either fix or explain each warning. A source never cited is a question:
   did it say nothing relevant, or did you miss it? Say which in the source register.

**Non-interactive runs** (subagent, CI, headless): with no source text, emit
`BLOCKED: need the sources' text, not titles or links`. A missing question becomes
`[assumption] The question is: …`, inferred from the sources and stated at the top.

## Useful references in this skill

- [`reference.md`](reference.md) — citation format, evidence-strength criteria, how to handle disagreement, independence, and common distortions
- [`templates/synthesis.md`](templates/synthesis.md) — the synthesis skeleton
- [`scripts/citations.py`](scripts/citations.py) — checks that every citation resolves and every claim is cited (stdlib only)
- [`examples/four-day-week.md`](examples/four-day-week.md) — worked example: four sources on a four-day-week pilot, the synthesis, and the checker's real output on a first draft and the fixed draft

## Quality bar

- **Every claim is cited to a source and a location.** The checker reports no errors; any warning left is explained.
- **Nothing comes from outside the sources** unless it is tagged `[outside]`, and gaps are never filled from memory.
- **Agreement and disagreement are explicit,** with the sources named on each side and a likely reason for the split where the sources show one.
- **Each finding has a strength rating and the criteria behind it.** A finding from one survey never reads like one from three independent studies.
- **Findings are no stronger than their sources.** Hedges survive; correlation stays correlation.
- **Gaps and what the sources do not say are listed** as specific statements.
- **Sources that aren't independent are counted once.**

## When to use this skill

- ✅ "Synthesise these six papers / reports / articles on X"
- ✅ Turning a set of interview transcripts into cited themes
- ✅ A literature review or evidence summary for a decision
- ✅ Checking where a set of analyst reports agree and where they don't

## When NOT to use this skill

- ❌ Deciding what to research, which sources to look for and when to stop — `research-plan`
- ❌ Ranking rival explanations for something that happened — `hypothesis-comparison`
- ❌ Turning one thread or transcript into a brief for another skill — `brief-intake`
- ❌ Pulling decisions and action items out of meeting notes — `decision-log`
- ❌ A market or competitor analysis with a framework — `strategy-analysis`
- ❌ Reviewing a document someone else wrote — `doc-critique`

## Anti-patterns to avoid

- ❌ **Source-by-source summaries.** "S1 says…, S2 says…" is an annotated list, not a synthesis. Organise by finding.
- ❌ **A citation with no location.** `[S2]` on a 60-page report can't be checked.
- ❌ **Smoothing over conflict.** "Results were mixed" hides which sources disagree and why.
- ❌ **Promoting hedges.** "May be associated with" becomes "drives" by the second paragraph.
- ❌ **Counting echoes.** Three news stories about one study are one source.
- ❌ **Filling gaps from memory.** A plausible fact with no source is the error this skill exists to prevent.
- ❌ **Citing a title you haven't read.** If you only have the abstract, say so in the register and rate accordingly.

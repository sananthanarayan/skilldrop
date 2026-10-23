---
name: source-synthesis
description: Answer a question from a set of sources the user supplied — papers, reports, articles, interview notes, emails — saying only what the material supports, labelling anything that comes from elsewhere where it appears, counting a source that repeats another once, and giving a labelled estimate when the user needs a figure the sources don't settle. Written in the length and format the user asked for; a full cited literature review only when that is the ask. Use when the user hands over several sources and asks to "synthesise these", "what do these papers say", "pull together what we know", "literature review", or "where do the sources agree and disagree".
---

# source-synthesis

**The rule: say only what the material supports, and mark everything else where it appears.**
The user handed over sources because they want to know what *those* say. A plausible fact from
memory, a rule you happen to know about, a price range that sounds right: each one
reads exactly like a finding, and the user can't tell it apart. The agent's habit is to fill
gaps helpfully. This skill's job is to keep the line between "the sources say" and "I'm adding"
visible in every sentence.

Two things follow from the rule:

- **A source that repeats another is one source.** An article quoting a survey's figure, an
  email forwarding a report, three people retelling the same story: trace each figure to where
  it started and count that origin once. Agreement between echoes is not agreement.
- **Hearsay and half-memories are reported as what they are.** "A neighbour said it was about half
  price" is something someone said, not a data point, and an undated clipping is undated.

## How to respond

1. **Answer the question first, in the user's terms.** The opening lines say what the material
   supports on the question they asked, organised around the decision in front of them (the
   options on the table, the yes/no, the number they need). Not source by source.

2. **Fit the size and format they asked for.** "Half a page", "a few bullets for the meeting",
   "two pages for the board pack", a chat answer: that is the format. Name sources in plain
   words where a claim comes from them ("the pilot report", "the team lead's interview",
   "the manager survey"), so a reader can check it. Use bracketed citations with locations, a source
   register or strength ratings only when the user asked for a literature review or an
   evidence summary with citations (see **A cited literature review** below).

3. **Check the sources before you trust them.**
   - Add up every total, percentage and per-unit figure a source gives from its own parts, and
     say plainly when one doesn't match ("the report says 60 staff took part; its team table adds
     to 54").
   - Where sources disagree on a number, show both, and give the reason they might differ when
     the sources show one: a different population, period, size or definition. Say which one
     fits the user's situation better and why. Don't average them.
   - Keep each source's hedges. "Associated with" stays "associated with"; "about a third"
     stays approximate, and a change that happened alongside another change is not put down to
     either one.

4. **When they need a figure the sources don't settle, estimate it and label it.** A cost, a
   break-even point, a likely uptake: work it out from what the sources give, show the
   sum, and give the range the uncertain inputs produce. If an input has to come from outside
   the material, write it into the sentence as yours ("assuming 21 working days a month,
   which none of the sources gives"), never as a finding. End with the one or
   two facts that would settle it. "The sources can't say" on its own is not an answer.

5. **Say what the material doesn't cover, once, briefly.** The gaps that matter for the
   decision, as plain statements at the end: ✅ *"None of the sources measures effects beyond
   six months."* Not a list of everything a perfect study
   would have measured.

6. **Deliver from what you have.** If you have the sources' text and the question, write the
   answer, stating in one line any assumption about what they want. Ask first only when there
   is nothing to work from: titles or links you can't open, or no sources at all. Then ask for
   the text in one or two plain sentences. Don't summarise a paper from its title or from
   memory.

7. **Keep the machinery out of the reply.** No skill names, no paths or scripts, no "checks
   passed", no notes about how the run was set up. The reply carries the answer. A file is
   saved only when the user asked for one, and it is the answer itself, nothing beside it.

## A cited literature review

When the user asks for a literature review, an evidence summary with citations, or findings
"every claim cited", produce the full form: a source register, findings grouped by theme with
`[S1:p4]` citations to a location, agreement and disagreement named source by source, an
evidence-strength rating with its criteria, and the gaps. Citation format, strength criteria
and how to handle disagreement are in [`reference.md`](reference.md); the skeleton is
[`templates/synthesis.md`](templates/synthesis.md); a worked example is
[`examples/four-day-week.md`](examples/four-day-week.md).

Before you hand it over, run the citation checker on the saved draft and fix what it reports:

```bash
# Claude Code
python3 "${CLAUDE_SKILL_DIR}/scripts/citations.py" synthesis.md
# Other IDEs (from the skill folder)
python3 scripts/citations.py synthesis.md
```

It reports citations that don't resolve, claims with no citation, citations with no location
and sources never cited. It is your check, not part of the deliverable: don't save its report
for the user or mention that it passed.

## Quality bar

- **Nothing reads as coming from the sources that doesn't.** Every outside input is marked as
  outside in the sentence where it appears; no gap is filled from memory.
- **Echoes are counted once.** A figure repeated by a second source is traced to its origin.
- **The sources' own sums are checked,** and any that don't add up are named.
- **The answer opens the reply and fits the requested size and format.**
- **A needed figure gets a worked, labelled estimate** with its range and what would settle it,
  not a refusal.
- **Findings are no stronger than their sources.** Hedges, approximations and confounds
  survive; hearsay stays hearsay.

## When to use this skill

- ✅ "Here's everything I've collected — what do we actually know?"
- ✅ "Synthesise these six papers / reports / articles on X"
- ✅ Turning interview notes or transcripts into what they show, with the disagreements kept
- ✅ A literature review or evidence summary for a decision

## When NOT to use this skill

- ❌ Deciding what to research, which sources to look for and when to stop — `research-plan`
- ❌ Ranking rival explanations for something that happened — `hypothesis-comparison`
- ❌ Turning one thread or transcript into a brief for another skill — `brief-intake`
- ❌ Pulling decisions and action items out of meeting notes — `decision-log`
- ❌ A market or competitor analysis with a framework — `strategy-analysis`
- ❌ Reviewing a document someone else wrote — `doc-critique`

## Anti-patterns to avoid

- ❌ **The helpful outside fact.** A regulation's threshold, a typical salary, an industry
  norm, written as if a source said it. Label it in the sentence, or leave it out.
- ❌ **Counting echoes.** "Two sources agree on 63%" when the second one is quoting the first.
- ❌ **Stopping at "the sources can't say".** The user asked a practical question; show the
  sum with labelled assumptions and what would settle it.
- ❌ **A research report for a meeting note.** Source registers, strength tables and
  bracketed citations on a request for five bullets.
- ❌ **Source-by-source summaries.** "S1 says…, S2 says…" is a list, not an answer. Organise by
  the decision.
- ❌ **Taking a source's total on trust.** Add it up.
- ❌ **Promoting hedges.** "May be associated with" becomes "drives" by the second paragraph.
- ❌ **Machinery in the reply.** "Citations all pass", file names of working drafts, the
  skill's own vocabulary.

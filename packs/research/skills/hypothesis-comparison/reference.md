# hypothesis-comparison — reference

## Where the method comes from

Analysis of competing hypotheses (ACH) was set out by Richards J. Heuer Jr. in *Psychology of
Intelligence Analysis* (CIA Center for the Study of Intelligence, 1999), chapter 8. The core
idea: people tend to pick the most likely explanation and look for evidence that supports it.
ACH reverses that. You set every hypothesis against every piece of evidence and look for the
hypothesis with the least evidence **against** it, because a single solid inconsistency can
rule a hypothesis out, while any amount of consistent evidence can't prove one.

Heuer's steps, in short:

1. Identify the possible hypotheses, ideally with a group so you get real rivals.
2. List the significant evidence and arguments, including assumptions and the *absence* of
   evidence you'd expect.
3. Build a matrix with hypotheses across the top and evidence down the side. Judge each item's
   consistency with each hypothesis, and how diagnostic it is.
4. Refine the matrix: reword or merge hypotheses, and set aside evidence that isn't
   diagnostic.
5. Draw tentative conclusions by trying to disprove hypotheses, not prove them.
6. Check how sensitive the conclusion is to a few critical items of evidence. What if they
   were wrong, misread, or planted?
7. Report the conclusion, with the relative likelihood of every hypothesis, not just the winner.
8. Name milestones: future observations that would show events are taking a different course.

This skill follows those steps. Two parts are this skill's own conventions, not Heuer's: the
0.5–2 weight scale, and the scoring rule in the script (`I` = 1 × weight, `II` = 2 × weight).

## Rating a cell

Ask: **"If this hypothesis were true, how likely is it that we'd see this?"** Don't ask
whether the evidence "supports" the hypothesis.

| Rating | Use when | Example (H: "the checkout release broke payment on iOS Safari") |
|---|---|---|
| `CC` | The hypothesis predicts this specifically; other causes rarely produce it | Payment SDK errors on iOS Safari start at the release minute |
| `C` | You would expect to see this if the hypothesis were true | More "button not working" tickets after the release |
| `N` | The hypothesis says nothing either way | A competitor ran a promotion |
| `NA` | The evidence doesn't apply to this hypothesis | — |
| `I` | You would not expect this if the hypothesis were true | The synthetic iOS Safari checkout test passes every run |
| `II` | This could hardly happen if the hypothesis were true | Payment SDK error rate on iOS Safari is flat across the release |

Rules:

- **Rate across a row.** Finish one piece of evidence against every hypothesis before the next.
- **Rate the evidence as reported,** then use the weight for how far you trust it. Don't
  hedge a rating to `N` because the source is weak.
- **Absences are evidence.** "No rise in support tickets" is `I` for any hypothesis that
  says customers hit an error.
- **Timing is rarely diagnostic.** "It started right after X" is `C` for X and for anything
  else that changed that day. List the other changes.

## Weighting

The weight is credibility × relevance, kept coarse:

| Weight | Typical source |
|---|---|
| 2 | A primary system record (payment ledger, server logs, a controlled test) that bears directly on the question |
| 1 | A reliable secondary source or a dashboard whose definition you know |
| 0.5 | Hearsay, a single anecdote, a dashboard whose definition changed, or evidence only loosely related |

Say why for any weight other than 1. If you can't say, use 1.

## Diagnosticity

A piece of evidence is **diagnostic** when it is rated differently for different hypotheses.
Evidence rated the same for all of them (all `C`, or a mix of `C` and `N` that adds no
inconsistency) can't move the ranking, however convincing it feels. These rows are the trap
ACH exists to expose: they are usually the reasons people give for the favourite hypothesis.

## Linchpins and sensitivity

A linchpin is a row whose removal changes which hypothesis ranks first. For each one:

- Where did it come from, and could it be wrong, out of date, or measured differently?
- Was it rated right? Re-read the row with a sceptic's eye.
- What's the cheapest way to confirm it?

If the conclusion rests on a linchpin you can't confirm, report the ranking as a lead.

## Confidence words

Use one word and give the reason:

- **High:** the leader has no `I` or `II` from weight-2 evidence, the runner-up has several,
  and no single row decides it.
- **Moderate:** the leader is clearly ahead, but rests on one or two linchpins, or the
  evidence is mostly weight 1.
- **Low:** a tie, a gap of 1 or less, or a ranking that flips when one weak row is removed.

## Failure modes

- **Too few hypotheses.** A matrix with two rivals mostly confirms the one you started with.
- **Hypotheses that aren't exclusive.** If two can both be true, say so; the matrix then shows
  which one has less against it, not that the other is false.
- **Evidence that is really an inference** ("the release was buggy"). Break it down to what
  was observed.
- **Deception or missing data.** If a source could be biased or the data is incomplete, add a
  row for the gap and weight the source down.

## When ACH is the wrong tool

- The cause is already confirmed by a direct test. Write it up instead.
- The question is about choosing a future option. Use a weighted comparison.
- There is almost no evidence. Plan the research first; a matrix of guesses ranks guesses.

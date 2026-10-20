---
name: judge-audit
description: Audit whether an LLM-as-judge, or a panel of judges, can be trusted for the decision its scores drive, before anyone acts on them — above all whether the judge errs differently on the variants being compared (prompt v1 vs v2, model A vs B, short vs long inputs), plus chance-corrected and weighted agreement with expert labels, precision and recall on a rare class, each run reported separately with the items that flipped, position and length bias, and confidence intervals, checked against the user's own gate or criterion and ending in a direct answer (ship or not, which judge to use). Use when the user asks "can we trust our LLM judge", "is our grader reliable enough to gate releases", "the grader says v2 is better, can we ship it", "which is the cheapest judge we can switch to", "our two judges agree 90%, is that good", "can we turn on auto-remove", "check our judge for position bias", or has a file of judge scores and wants to know whether to act on them.
---

# judge-audit

Decides whether a judge's scores are good enough for one named decision, from the judgements
themselves, and answers the question the user asked. A grader can match an expert well overall
and still over-score the very variant it is being used to pick. This skill audits judgements that
already exist; designing the eval set and grading plan is `llm-eval-harness`, generating eval
cases for a skill is `eval-harness-generator`, and measuring AI tool usage is `ai-usage-report`.

## How to respond

**Four rules come before the steps and outrank them:**

- **Answer what was asked, first.** Open with the answer, the decision or the artifact, in plain words. Scores, matrices, frameworks and tags come after it, and anything that doesn't change the answer is cut.
- **Use only what you were given.** Don't add facts, names, numbers, incidents, history, steps or sections the input doesn't contain. What you need and don't have is left out of the artifact and listed once at the end under "To confirm".
- **Deliver from what you have.** When the request gives you something to work on, state your assumptions in a line and produce the result. When it gives you nothing to work on, ask for it in one or two plain sentences and say what you will do once you have it.
- **Write for someone who has never heard of this skill.** No skill names, no paths or scripts from this folder, no internal terms, and nothing about how the run was set up. A next step is one plain sentence at the end that describes the work.
- **For this skill:** The pass mark is the user's, never yours. Judge the numbers against the gate or criterion the user or their files state; when there is none, say what the numbers do to their decision. A threshold the input doesn't contain ("kappa ≥ 0.6", "n ≥ 100") never decides the answer.

1. **Pin the decision, the user's criterion, and the comparison.** Find the decision (rank
   variants, publish a number, gate a release, act on single items) and the criterion the user
   or their files give: ✅ *"Gate: a build ships if its precision@5 is within 2.0 points of
   production; the change compares short against long documents."* Read every file for it
   (READMEs, run notes) before asking. No criterion stated: no pass mark, and the answer says
   what the errors would do to the decision. Name the variable the decision compares: version,
   model, arm, or a property the planned change shifts (length, language).

2. **Compute, don't estimate.** Run the script, grouped by the compared variable, with the
   user's criterion as `--gate`:

   ```bash
   # Claude Code
   python3 "${CLAUDE_SKILL_DIR}/scripts/judge_stats.py" grades.csv --group-by prompt_version
   python3 "${CLAUDE_SKILL_DIR}/scripts/judge_stats.py" run_1.jsonl run_2.jsonl --gold gold.csv --map true=violation,false=ok --positive violation
   # Other IDEs (from the skill folder)
   python3 scripts/judge_stats.py wide.csv --judges big,small --positive relevant --group-by "tokens>=400" --gate "bias_diff<=2.0"
   ```

   Several files are one run each, joined on the item id with columns resolved per file;
   `--gold` reads expert labels from their own file; `--judges` reads one column per judge;
   `--map` renames labels that mean the same; `--col` maps any other column. Given only counts,
   rebuild one row per item and run it anyway; without a shell, use the formulas in
   [`reference.md`](reference.md) and show the arithmetic.

3. **Quote every number from the output, with its subset, run and n.** All-rows and
   labelled-rows figures are different numbers; so are run 1 and run 2. ✅ *"On the 20 items the
   reviewer scored, the grader averages 3.7 against her 3.1."* — ❌ a run-1 false-positive count
   presented as the result when run 2 has more. No figure appears that the output doesn't print.

4. **Use the scale and the metric the user uses.** For 1–5 scores report quadratic-weighted
   kappa (say "quadratic"), exact agreement and mean bias; unweighted kappa treats 4-vs-5 like
   1-vs-5. Pass `--threshold` only when the user stated a pass score. When the user quotes a
   figure ("kappa 0.8", "they agree 80%"), reproduce it first, say which statistic it is on which
   rows, then show what it hides.

5. **Lead with the differential.** Per variant compare exact agreement, bias judge − expert
   with its interval, how often the judge scores higher and lower, and the bias-vs-length
   correlation; then the judge's v2 − v1 gain against the expert's own on the labelled rows. ✅
   *"It matches the reviewer on 18 of 20 A answers but 9 of 20 B answers and over-scores B by
   +0.55 [+0.30, +0.80]; her own scores show B ahead by +0.10 (interval spans zero)."* When the
   bias tracks a property the planned change shifts, the shift in bias is what lands on the gate.

6. **Chance-correct agreement, and on a rare class count the rare class.** Two raters who each
   say "pass" 90% of the time agree 82% by chance: ✅ *"Raw 88%, chance 80%, kappa 0.40."* With
   one class under about 15%, lead with how many expert positives exist, the confusion counts,
   recall and precision with intervals; accuracy only beside the always-majority baseline. ✅
   *"6 of 120 posts are violations, so always saying 'fine' scores 95%. It caught 4 of 6 (30%–90%)
   and flagged 2 fine posts."* — ❌ *"96% accurate, so it's reliable."*

7. **With repeated runs, report each run, then the flips.** One row per run: precision, recall,
   false positives. Then run-against-run agreement joined on the item id, the items that
   flipped and which of them the expert labels positive, and what was caught in both runs. ✅
   *"Run 1 wrongly flagged 1 post, run 2 flagged 2; 5 posts changed verdict, 2 of them real
   violations."* Files in different row orders or formats are joined on id, never by line.

8. **For pairwise judges, read the order column before the win rate.** State the direction from
   the counts: ✅ *"The first-shown answer won 70 of 100; the new variant went first on 15 of 25
   questions."* Report the order-balanced win rate per judge; the unit is the question, not the
   judgement. An interval excluding 50% does not fix an order confound; judging both orders does.

9. **Measure stability and judge-to-judge agreement across every trial.** Flip rate per judge,
   with the flipped items named; trial-matched kappa between judges, and Fleiss' across every
   judge × trial rating. Judges sharing a blind spot agree on it: expert agreement ranks first.

10. **Say what the data cannot measure, in one line.** One run: no flip rate. One expert: no
    expert-expert baseline. No expert labels: nothing shows the judge is right. Never fill a gap
    with a guess.

11. **Answer the question asked, against the user's criterion.** Each gate check reads
    *clears* (whole interval meets it), *fails* (none of it does) or *can't tell* (the interval
    spans it). "Which judge can we use" names one: ✅ *"Switch to the mid tier: it is the cheapest
    judge whose error doesn't move with length (bias shift −2 points against a 2.0-point gate);
    the small tier says relevant to 9 of 10 long passages the reviewer rejected."* — ❌ *"None
    can be recommended until 100 more labels exist."* Conditions are actions with an n (label 30
    more long passages); a small sample widens the interval, it doesn't withhold the answer.
    When the judge in use today also reads *can't tell*, the sample can't certify anyone: compare
    the candidate with the incumbent on the same items (the accuracy difference and its interval).
    Kappa bands (Landis–Koch "moderate") appear only as labelled context, never as the reason.
    Verdict words: **TRUSTWORTHY FOR THIS DECISION**, **USE WITH CONDITIONS**, **DO NOT RELY ON IT**.

12. **Write the reply short.** First line: the answer (yes/no, which judge, which arm it
    favours and by how much). Then the two to four numbers behind it, each with its subset and
    run; what can't be measured; one next step that fits the user's deadline. No kappa tutorial,
    no tables unless asked. A chat question gets a chat answer.

**Non-interactive runs** (subagent, CI, headless): no criterion in the input becomes
`[assumption] no stated gate; the reply says what the errors do to the decision`; a compared
variable the input does not name becomes `[assumption] no grouping`. No judgements and no counts
emit `BLOCKED: need the per-item judgements (item, judge, label or score) or the agreement
counts`, because a verdict without them is invented.

## Useful references in this skill

- [`reference.md`](reference.md) — turning the user's gate into the number that answers it, kappa (unweighted, weighted, Fleiss') and Wilson formulas with worked tables, the both-orders protocol, and every input shape the script reads
- [`scripts/judge_stats.py`](scripts/judge_stats.py) — per-group, per-run and pooled agreement, weighted kappa, rare-class precision and recall, flips joined on item id, position and length bias, `--gate` (stdlib only; `--self-test` checks the maths)
- [`examples/summary-panel.md`](examples/summary-panel.md) — worked example: a three-judge panel on summary faithfulness, a USE WITH CONDITIONS verdict

## Quality bar

- **The first line answers the question asked:** ship or not, which judge, which arm it favours.
- **The criterion is the user's;** with none, no invented pass mark decides anything.
- **Statistics are stratified by the compared variable** before any pooled figure is quoted.
- **Ordinal scores get weighted kappa, named as quadratic or linear.**
- **A rare class gets its count, confusion, recall and precision with intervals,** not accuracy.
- **Each run is reported on its own, with the flips,** joined on item id.
- **Every number matches the output for the subset and run it is labelled with,** n included.
- **What the data cannot measure is named,** never estimated.

## When to use this skill

- ✅ "The grader says v2 beats v1 — can we ship on it?" with a file of scores
- ✅ "Which is the cheapest judge we can switch to?" with several judges on the same items
- ✅ "It's 96% accurate on two runs — can we turn on auto-remove?"
- ✅ A pairwise A/B judged by a model, before shipping the winner
- ✅ "Our two graders agree 90%, good enough?"

## When NOT to use this skill

- ❌ Designing the eval set, grading methods and pass bar for an LLM feature — `llm-eval-harness`
- ❌ Generating eval cases for a skill's `evals/` folder — `eval-harness-generator`
- ❌ Measuring how much teams use AI tools — `ai-usage-report`
- ❌ Inter-rater reliability for humans only, with no model in the loop — the statistics transfer, but the bias checks here assume a model

## Anti-patterns to avoid

- ❌ **An invented gate.** "Kappa must be ≥ 0.6 with n ≥ 100" when the user's gate is a 1.0-point tolerance.
- ❌ **Refusing to pick.** "Which is cheapest?" answered with "none yet" instead of a name and a condition.
- ❌ **Run 1 as the result.** Two runs are two rows, then the flips.
- ❌ **Joining runs by line number.** Rows in a different order make a line-by-line kappa meaningless.
- ❌ **Accuracy on a rare class.** 96% when 95% is the always-"fine" score.
- ❌ **A pooled kappa for a comparison,** or unweighted kappa on a 1–5 scale.
- ❌ **Position bias stated backwards,** or judgements counted as the unit instead of questions.
- ❌ **Leading with the stats dump.** The reader asked whether to act; tell them, then show why.

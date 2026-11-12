# Worked example — a three-judge panel for a summary-faithfulness dashboard

## Input given to the skill

> We run three LLM judges (judge-x, judge-y, judge-z) over our article summaries and score each
> one 1–5 for "faithful to the article". 4 or 5 counts as a pass. Ines, our senior editor,
> marked 45 summaries pass/fail herself. Every judge scored every summary twice. From next month
> we want to put the panel's average pass rate on the newsroom quality dashboard instead of
> Ines's weekly spot check. Scores are in `panel.csv` (item, judge, trial, score, expert,
> length). Can we?

The file has 270 rows: 45 summaries × 3 judges × 2 trials, Ines's label on every summary, and
the summary's word count.

## What was run

```bash
python3 scripts/judge_stats.py panel.csv --threshold 4
```

Excerpt of the output the reply rests on:

```
| judge-x | all labelled | 45 | 87% [74%, 94%] | 56% | 0.70 [0.44, 0.90] |
| judge-y | all labelled | 45 | 87% [74%, 94%] | 57% | 0.69 [0.43, 0.90] |
| judge-z | all labelled | 45 | 78% [64%, 87%] | 56% | 0.50 [0.21, 0.75] |
- judge-x passes 3 of 15 items the expert failed (20% [7%, 45%])
- judge-x and judge-y agree on 39 expert-labelled items; on 3 of them both are wrong (S04, S33, S38).
**Fleiss' kappa** (first trial per judge), 3 raters on 45 items: 0.56 [0.34, 0.75]
| judge-x | 45 | 1 | 2% [0%, 12%] | S11 |
| judge-y | 45 | 2 | 4% [1%, 15%] | S17, S35 |
| judge-z | 45 | 9 | 20% [11%, 34%] | S02, S06, S13, S19, S21, S31, S34, S36, S40 |
| judge-x | 45 | -0.09 [-0.39, 0.20] |
| expert | 45 | -0.03 [-0.32, 0.26] |
```

---

## Output

**Use it with conditions: judge-x on its own is close to good enough for the dashboard number,
judge-z is pulling the panel down, and 15 failed summaries are too few to know how often the
judges miss an unfaithful one.**

- **judge-x and judge-y match Ines well.** Each agrees with her on 87% of the 45 summaries,
  where about 56% would match by chance: kappa 0.70 (95% interval 0.44–0.90) and 0.69.
  judge-z reaches 0.50 (0.21–0.75).
- **judge-z is unstable.** Scored twice, it changed its verdict on 9 of 45 summaries (20%);
  judge-x changed 1, judge-y 2. With it in, the three judges agree with each other at
  only 0.56 (Fleiss' kappa), against 0.69 for judge-x and judge-y alone.
- **The miss rate is not pinned down.** judge-x passed 3 of the 15 summaries Ines failed
  (20%), but with 15 the true rate could be anywhere from 7% to 45%.
- **All three judges passed S33 and S38**, which Ines failed, and all three failed S04, which
  she passed. Three judges agreeing on those is one blind spot, not three opinions.
- **Length isn't driving the scores:** judge-x's correlation with word count is −0.09, Ines's
  −0.03.

**Conditions before the number goes on the dashboard**

1. Report judge-x's pass rate (judge-y as a cross-check), not the three-judge average.
2. Decide how many unfaithful summaries the dashboard can count as faithful; with 15 of
   Ines's failures the miss rate could be 7% or 45%, and more of her failures is what narrows it.
3. Read S33 and S38 to see what the judges miss, and add that to the scoring instructions.

**Can't conclude yet:** whether judge-x misses 1 in 10 unfaithful summaries or 4 in 10.

To confirm: the miss rate the newsroom accepts on the dashboard number.

Next step: have Ines mark more of the summaries she expects to fail, re-run the comparison,
and switch the dashboard to judge-x if its miss rate sits inside what the newsroom accepts.

# judge-audit reference

## Reading the numbers against the decision

There is no universal pass mark for a judge. The criterion is the user's: a gate tolerance ("no
more than 1.0 point below production"), a recall target, a number of wrongful removals they can
live with. Translate the numbers into that criterion; when they gave none, say what the numbers
do to their decision and stop there.

| The user's decision | The number that answers it | `--gate` form |
|---|---|---|
| A tolerance on a difference between two arms (precision@5 within 1.0 point, mean score +0.3) | how much the judge's bias differs between the arms, in the same units, with its interval | `bias_diff<=1.0` with `--group-by` on what separates the arms |
| Act automatically on one class (remove, block, escalate) | recall on that class (what slips through) and false positives (what is wrongly acted on), per run | `recall>=0.9`, `false_positives<=0` |
| Publish one rate (pass rate, relevance rate) | the judge's rate minus the expert's, in points | `bias<=2` |
| Swap a judge for a cheaper one | the same check per judge; the cheapest judge that meets the user's criterion is the answer | any of the above |

Outcomes per judge and run: **clears** (the whole 95% interval meets the criterion), **fails**
(none of it does), **can't tell** (the interval spans it; say which side the point estimate is on
and how many more labelled items of the scarce class would narrow it).

Kappa bands (Landis and Koch, 1977: 0.41–0.60 "moderate", 0.61–0.80 "substantial") are labels
someone chose, not evidence. Quote one only as context, named as that convention, and never as
the reason to ship or block.

**Translating a difference gate.** A judge with the same bias on both arms leaves a difference
intact, whatever its overall accuracy. A judge whose bias moves with something that differs
between the arms (passage length, reply length, variant) adds that movement to the difference.
When a planned change shifts that property (re-chunking to long passages, a prompt that writes
longer replies), the shift in bias is what lands on the gate: compare it with the tolerance.

## Formulas for hand computation

**Cohen's kappa** for two raters on the same n items:

```
p_o = (items where both gave the same label) / n
p_e = sum over labels k of (share rater 1 gave k) × (share rater 2 gave k)
kappa = (p_o - p_e) / (1 - p_e)
```

Worked: 50 items. Both "yes" on 20, both "no" on 15, rater 1 yes and rater 2 no on 5, the
reverse on 10. p_o = 35/50 = 0.70. Rater 1 says yes 25/50 = 0.5, rater 2 says yes 30/50 = 0.6,
so p_e = 0.5 × 0.6 + 0.5 × 0.4 = 0.50. kappa = (0.70 − 0.50) / 0.50 = 0.40. The bootstrap
interval on these 50 items runs from about 0.12 to 0.64.

**Weighted kappa** for ordinal scores (1–5 and the like), on numeric scores a (judge) and b
(expert), disagreement d = (a − b)² for quadratic, |a − b| for linear:

```
D_o = mean over items of d(a_i, b_i)
D_e = sum over score pairs x, y of (share judge gave x) × (share expert gave y) × d(x, y)
kappa_w = 1 - D_o / D_e
```

Worked, 10 items on a 1–3 scale: both 1 on 2, both 2 on 3, both 3 on 2, and one each of
(judge 1, expert 2), (2, 3), (3, 1). Each rater's shares are 0.3 / 0.4 / 0.3.
Quadratic: D_o = (1 + 1 + 4) / 10 = 0.6; D_e = 2 × (0.3·0.4·1 + 0.3·0.3·4 + 0.4·0.3·1) = 1.2;
kappa = 1 − 0.6 / 1.2 = **0.50**. Linear: D_o = 0.4, D_e = 0.84, kappa = 11/21 = **0.52**.
Unweighted on the same table: p_o = 0.7, p_e = 0.34, kappa = 6/11 = **0.55**. On pass/fail data
all three coincide. `judge_stats.py --self-test` checks the script against these values.

**Mean bias** = mean of (judge − expert) on the items both scored, with a bootstrap interval.
Per group, compare it across the variants: a difference in bias between arms is a difference the
judge adds to the comparison by itself.

**Fleiss' kappa** for m raters on N items, n_ij = raters who gave item i label j:

```
P_i  = (sum_j n_ij² - m) / (m(m - 1))
Pbar = mean of P_i
p_j  = sum_i n_ij / (N m)
P_e  = sum_j p_j²
kappa = (Pbar - P_e) / (1 - P_e)
```

**Wilson 95% interval** for k successes in n:

```
centre = (p + z²/2n) / (1 + z²/n)
half   = z × sqrt(p(1-p)/n + z²/4n²) / (1 + z²/n),   z = 1.96
```

**Bootstrap** for kappa or a correlation: resample items with replacement, recompute, take the
2.5th and 97.5th percentiles of 2,000 resamples. Resample items, not judgements, so repeated
trials of one item move together.

**False-pass rate** = items the expert failed that the judge passed ÷ items the expert failed.
**False-fail rate** = items the expert passed that the judge failed ÷ items the expert passed.

**Order-balanced win rate** for variant X = (X's win rate when shown first + X's win rate when
shown second) / 2. An unbiased judge gives the same two rates.

## Why kappa drops when one label dominates

When 90% of items pass, two raters agree 82% by chance, so a high raw agreement leaves kappa
little room. That is the point, not a flaw: most of the agreement is free. When the skew is 85%
or more, report the confusion counts, precision and recall on the rare class beside kappa, and
how many rare-class items the sample holds: 6 positives give a recall interval of roughly 30% to
90% even at 4 of 6. Accuracy against an always-majority baseline of 95% says almost nothing.

## Both-orders protocol for pairwise judges

1. Judge every pair twice, once in each order, at the same settings.
2. Count a win only when the same output wins in both orders; a split is a tie.
3. Report the share of pairs that split: that is the position effect, measured directly.
4. With one order per pair, randomise it and check that each variant is shown first close to
   half the time; if not, use the order-balanced rate.

## Separating criteria

A holistic score ("is this a good reply?") lets fluency stand in for correctness. When the
judge's score tracks length more than the expert's does, split the rubric into criteria a judge
can check one at a time, and gate on the ones that matter:

- ✅ *"Policy-correct (yes/no) · answers the question asked (yes/no) · tone (1–5)."* Gate on the
  two yes/no criteria; report tone.
- ❌ *"Rate the reply 1–10 for quality."*

Re-run the audit on each criterion separately: a judge can be reliable on tone and useless on
correctness.

## Input columns the script reads

One row per judgement, CSV or JSONL. Column names are case-insensitive.

| Column | Required | Meaning |
|---|---|---|
| `item` | yes | the thing judged (aliases: `item_id`, `id`, `case`, `ticket_id`, `question_id`, `passage_id`, `post_id`) |
| `label` | one of label/score | the verdict; in pairwise data, the variant chosen or `tie` (aliases: `verdict`, `winner`, `choice`, `flagged`, `decision`, `prediction`) |
| `score` | one of label/score | numeric score (aliases: `judge_score`, `grader_score`); `--threshold T` makes score ≥ T a pass, only when the user stated T |
| `judge` | no | absent means every row is one judge (aliases: `model`, `grader`, `rater`) |
| `trial` | no | repeat number; default 1 (aliases: `run`, `repeat`) |
| `expert` | no | the expert's label or score for the item, on any of its rows (aliases: `human`, `gold`, `gold_label`, `expert_label`, `human_score`) |
| `position` | no | pairwise: where the **chosen** output was shown (`A`/`B`, `1`/`2`, `first`/`second`) |
| `first_shown` | no | pairwise: which **variant** was shown first (aliases: `shown_first`, `first_variant`) |
| `length` | no | pointwise: length of the judged output; pairwise: length of the chosen output (aliases: `words`, `reply_words`, `word_count`) |
| `other_length` | no | pairwise: length of the output not chosen |

Shapes the script also reads:

- **One file per run.** `judge_stats.py run_1.jsonl run_2.jsonl` makes each file a run, in the
  order given, and resolves columns per file, so `item_id`/`flagged` in one and `id`/`verdict`
  in the other both work. Runs are joined to each other and to the expert **on the item id**;
  the output says when the files list items in different orders. A line-by-line comparison of
  two files in different orders measures nothing.
- **Expert labels in their own file:** `--gold gold.csv` (an item column plus an expert, label or
  score column).
- **One column per judge:** `--judges col_a,col_b,col_c` reads a wide file where each named
  column holds that judge's label for the row's item.
- **Different words for the same label:** `--map true=violation,false=ok` renames before
  anything is compared. Labels that differ only in case (`VIOLATION`, `violation`) merge on their
  own. The output flags a run whose labels share no value with the expert's.

Any other name maps with `--col NAME=COLUMN` (for example `--col score=grader_points`).
`--group-by COL` repeats every statistic per value of COL; `--group-by "COL>=N"` splits a numeric
column in two (`passage_tokens>=400`). It leads with a comparison table and the between-group
differences (judge mean or rate, expert mean or rate, bias), each with an interval that resamples
items within each group; for two-label data the differences are in percentage points of the
`--positive` class's rate.

On two-label data `--positive` names the class the decision acts on or counts (`violation`,
`relevant`, `pass`); without it, `pass`/`yes`/`good` when present, else the expert's minority
class. Every run then gets its own row: judge and expert counts of that class, TP/FP/FN/TN,
precision, recall and false-positive rate with Wilson intervals, and accuracy beside the
always-majority baseline. False-pass rate on pass/fail data is that false-positive rate.

`--gate SPEC` (repeatable) checks the user's criterion per judge and run. Metrics: `accuracy`,
`kappa`, `quadratic`, `precision`, `recall`, `fpr`, `false_positives`, `false_negatives`,
`flip_rate`, `bias` (score points, or percentage points of the positive rate), `bias_diff`
(needs `--group-by`). Rates take `0.9` or `90%`.

Between judges, repeats add a trial-matched kappa (pooled and per trial) and Fleiss' kappa
across every judge × trial rating; with expert labels, the accuracy difference between two
judges on the same items, with its interval. Pairwise rates count ties as judgements no variant
won, and their intervals resample questions, not judgements. Exit code 2 means the input could
not be read, with the reason on stderr.

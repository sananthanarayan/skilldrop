#!/usr/bin/env python3
"""Agreement, stability and bias statistics for LLM-as-judge records.

Reads a CSV or JSONL file with one row per judgement and reports:
  - each judge's label distribution (and the expert's, when given)
  - agreement with expert labels: exact agreement (Wilson interval), Cohen's
    kappa, and for ordinal scores (1-5 and the like) quadratic- and
    linear-weighted kappa, within-one agreement, mean judge, mean expert and
    mean bias (judge - expert) on the same rows, how often the judge scores
    higher or lower, and the bias-vs-length correlation; false-pass and
    false-fail rates when the labels are pass/fail-like
  - agreement between judges: on first trials, and matched trial by trial
    (pooled and per trial) when there are repeats; Fleiss' kappa for three
    or more judges, and across every judge x trial rating
  - test-retest stability: per judge, the share of items whose label changed
  - pairwise data (a `position` or `first_shown` column): how often the
    first-shown output wins, each variant's win rate when shown first and
    second, the order-balanced win rate, how order was assigned per item, and
    win rates with intervals bootstrapped over items (the unit of analysis)
  - length bias, when a length column exists
  - with --group-by COL (or COL>=N to split a numeric column in two): every
    statistic above per value of COL (version, arm, length band), led by a
    comparison table and the between-group differences in judge mean or rate,
    expert mean or rate, and bias, so a judge that errs differently on the
    variants being compared is visible
  - two-label data (pass/fail, violation/ok, relevant/irrelevant): per judge
    AND PER RUN, the confusion counts against the expert, precision, recall
    and false-positive rate on the class the decision acts on (Wilson
    intervals), how many expert positives the sample holds, and accuracy
    beside the always-majority baseline
  - several runs, one file each (columns may differ between files): every
    run is joined to the others and to the expert on the item id, never on
    line order; each run is reported separately, then the items that flipped
  - --gate SPEC: the user's own criterion, checked per judge and run against
    the point estimate and the whole interval (clears / fails / can't tell)

Columns (case-insensitive; aliases in brackets; --col NAME=COLUMN overrides):
  item         required  [item_id, id, case, case_id, ticket_id, question_id, sample_id, passage_id]
  judge        optional; absent means one judge  [judge_id, model, rater, grader]
  label        required unless score is given  [verdict, grade, winner, preference, choice, flagged]
  score        optional numeric  [rating, judge_score, grader_score, model_score]
  trial        optional, default 1  [run, repeat]
  expert       optional, the human/expert label  [human, gold, human_score, expert_score, ...]
  position     optional, pairwise: where the CHOSEN output was shown (A/B, 1/2, first/second)
  first_shown  optional, pairwise: which VARIANT was shown first  [shown_first, first_variant]
  length       optional, pointwise: length of the judged output; pairwise: of the chosen one
               [words, tokens, chars, reply_words, word_count, length_chosen]
  other_length optional, pairwise: length of the output not chosen

Usage:
  python3 judge_stats.py judgements.csv
  python3 judge_stats.py grades.csv --group-by prompt_version
  python3 judge_stats.py run_1.jsonl run_2.jsonl --gold gold.csv --map true=violation,false=ok \
      --positive violation --gate "recall>=0.9"
  python3 judge_stats.py wide.csv --judges judge_big,judge_small --group-by "tokens>=400" \
      --positive relevant --gate "bias_diff<=1.0"
  python3 judge_stats.py judgements.jsonl --group-by judge --json -o stats.json
  python3 judge_stats.py scores.csv --threshold 4      # only a threshold the user stated
  python3 judge_stats.py judgements.csv --expert-judge lead-reviewer
  python3 judge_stats.py --self-test                   # check the maths on hand-computed tables
  cat judgements.csv | python3 judge_stats.py -

Exit codes: 0 report written, 1 self-test failed, 2 bad input.
"""

import argparse
import csv
import io
import json
import math
import random
import sys
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

ALIASES = {
    "item": ["item", "item_id", "id", "case", "case_id", "ticket_id", "ticket", "question_id",
             "question", "sample_id", "example_id", "passage_id", "post_id"],
    "judge": ["judge", "judge_id", "model", "rater", "grader", "judge_model", "grader_model"],
    "label": ["label", "verdict", "grade", "winner", "preference", "choice", "flagged", "decision",
              "prediction"],
    "score": ["score", "rating", "judge_score", "grader_score", "model_score", "llm_score"],
    "trial": ["trial", "run", "repeat"],
    "expert": ["expert", "human", "gold", "reference", "expert_label", "human_label",
               "human_score", "expert_score", "gold_label", "gold_score"],
    "position": ["position", "chosen_position", "winner_position"],
    "first_shown": ["first_shown", "shown_first", "first_variant", "order_first"],
    "length": ["length", "words", "tokens", "chars", "length_chosen", "reply_words", "word_count",
               "response_words", "n_words"],
    "other_length": ["other_length", "length_other", "length_rejected"],
}
POSITIVE = {"pass", "yes", "true", "correct", "good", "acceptable", "ok", "accept", "approved", "1"}
NEGATIVE = {"fail", "no", "false", "incorrect", "bad", "poor", "unacceptable", "reject", "rejected", "0"}
TIES = {"tie", "draw", "equal", "none", "same"}
FIRST = {"a", "1", "first", "left", "1st"}
SECOND = {"b", "2", "second", "right", "2nd"}
SMALL_N = 30
Z = 1.959964


def natural(s):
    """Sort key so R2 comes before R10."""
    out, num = [], ""
    for ch in str(s):
        if ch.isdigit():
            num += ch
            continue
        if num:
            out.append((0, int(num), ""))
            num = ""
        out.append((1, 0, ch))
    if num:
        out.append((0, int(num), ""))
    return out


def fail(msg):
    sys.stderr.write("error: " + msg + "\n")
    sys.exit(2)


# ---------- loading ----------

def read_rows(path):
    if path == "-":
        text = sys.stdin.read()
        name = "stdin"
    else:
        p = Path(path)
        if not p.is_file():
            fail("file not found: " + str(path))
        with p.open(encoding="utf-8-sig") as f:
            text = f.read()
        name = p.name
    if not text.strip():
        fail("the input is empty")
    if name.endswith(".jsonl") or text.lstrip().startswith("{"):
        rows = []
        for n, line in enumerate(text.splitlines(), 1):
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except ValueError as e:
                fail("line %d is not valid JSON: %s" % (n, e))
            if not isinstance(obj, dict):
                fail("line %d is not a JSON object" % n)
            rows.append({str(k).strip().lower(): ("" if v is None else str(v).strip())
                         for k, v in obj.items()})
        return rows
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        fail("the CSV has no header row")
    return [{(k or "").strip().lower(): (v or "").strip() for k, v in r.items()} for r in reader]


def resolve(rows, overrides, strict=True, used=None):
    keys = set()
    for r in rows:
        keys.update(r.keys())
    cols = {}
    for canon, col in overrides.items():
        if col not in keys:
            if strict:
                fail("--col %s=%s: no such column (columns: %s)" % (canon, col, ", ".join(sorted(keys))))
            continue
        if used is not None:
            used.add(canon)
        cols[canon] = col
    for canon, names in ALIASES.items():
        if canon in cols:
            continue
        for n in names:
            if n in keys and n not in cols.values():
                cols[canon] = n
                break
    return cols, keys


def to_float(s):
    try:
        x = float(s)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None


LABEL_MAP = {}


def norm_label(s):
    s = (s or "").strip()
    s = LABEL_MAP.get(s.lower(), s)
    x = to_float(s)
    if x is not None and x.is_integer():
        return str(int(x))
    low = s.lower()
    return low if low in POSITIVE or low in NEGATIVE or low in TIES else s


def parse_group(group_by):
    """'col' groups by value; 'col>=N' splits a numeric column into col<N and col>=N."""
    g = group_by.strip().lower()
    if ">=" in g:
        col, _, thr = g.partition(">=")
        t = to_float(thr.strip())
        if t is None:
            fail("--group-by %s: the value after >= must be a number" % group_by)
        return col.strip(), t
    return g, None


def group_value(r, gcol, gthr):
    raw = r.get(gcol, "")
    if gthr is None:
        return raw or "(blank)"
    x = to_float(raw)
    if x is None:
        return "(blank)"
    t = ("%g" % gthr)
    return "%s<%s" % (gcol, t) if x < gthr else "%s>=%s" % (gcol, t)


def load(path, threshold, expert_judge, group_by, overrides, trial_override=None, wide=None,
         used=None):
    rows = read_rows(path)
    if not rows:
        fail("no judgement rows found in " + str(path))
    cols, keys = resolve(rows, overrides, strict=used is None, used=used)
    warnings = []
    where = "" if trial_override is None else " in %s" % Path(path).name
    if "item" not in cols:
        fail("no 'item' column%s (accepted names: %s; or pass --col item=<column>)"
             % (where, ", ".join(ALIASES["item"])))
    if wide:
        missing = [c for c in wide if c not in keys]
        if missing:
            fail("--judges: no such column%s: %s (columns: %s)"
                 % (where, ", ".join(missing), ", ".join(sorted(keys))))
    elif "label" not in cols and "score" not in cols:
        fail("need a 'label' or a 'score' column%s (or pass --col label=<column>)" % where)
    if threshold is not None and "score" not in cols and not wide:
        fail("--threshold needs a 'score' column")
    if "judge" not in cols and not wide:
        warnings.append("no judge column%s: every row is treated as one judge named 'judge'" % where)
    gcol = gthr = None
    if group_by:
        gcol, gthr = parse_group(group_by)
        if gcol not in keys:
            fail("--group-by %s: no such column%s (columns: %s)"
                 % (group_by, where, ", ".join(sorted(keys))))

    recs, expert, order = [], {}, []
    for n, r in enumerate(rows, 2):
        item = r.get(cols["item"], "")
        if item and item not in order:
            order.append(item)
        cells = [(c, r.get(c, "")) for c in wide] if wide else [
            (r.get(cols["judge"], "") if "judge" in cols else "judge", None)]
        for judge, wide_val in cells:
            if not item or not judge:
                warnings.append("row %d skipped: empty item or judge" % n)
                continue
            if wide:
                raw_label, score = wide_val, to_float(wide_val)
            else:
                raw_label = r.get(cols["label"], "") if "label" in cols else ""
                score = to_float(r.get(cols["score"], "")) if "score" in cols else None
            if threshold is not None:
                if score is None:
                    warnings.append("row %d skipped: score is not a number" % n)
                    continue
                label = "pass" if score >= threshold else "fail"
            else:
                label = norm_label(raw_label)
                if not label and score is not None and not wide:
                    label = norm_label(r.get(cols["score"]))
            if not label:
                warnings.append("row %d skipped: no label for %s" % (n, judge))
                continue
            trial = trial_override or (r.get(cols["trial"], "") if "trial" in cols else "")
            rec = {"item": item, "judge": judge, "trial": trial or "1", "label": label,
                   "score": score, "position": None, "first": None, "length": None,
                   "other_length": None}
            if gcol:
                rec["group"] = group_value(r, gcol, gthr)
            fill_rec(rec, r, cols)
            recs.append(rec)
        if "expert" in cols:
            e = r.get(cols["expert"], "")
            if threshold is not None and to_float(e) is not None:
                e = "pass" if to_float(e) >= threshold else "fail"
            e = norm_label(e)
            if e and item:
                if item in expert and expert[item] != e:
                    warnings.append("item %s has conflicting expert labels (%s, %s); kept the first"
                                    % (item, expert[item], e))
                else:
                    expert[item] = e
    if expert_judge:
        keep = []
        for rec in recs:
            if rec["judge"] == expert_judge:
                expert.setdefault(rec["item"], rec["label"])
            else:
                keep.append(rec)
        recs = keep
    if not recs:
        fail("no usable judgement rows in " + str(path))
    if expert_judge and not expert:
        fail("--expert-judge %s matched no rows" % expert_judge)
    return recs, expert, cols, warnings, order


def load_gold(path, threshold, overrides):
    """Expert labels from their own file: an item column and an expert (or label/score) column."""
    rows = read_rows(path)
    cols, keys = resolve(rows, overrides, strict=False)
    if "item" not in cols:
        fail("--gold: no item column in %s (accepted names: %s)" % (path, ", ".join(ALIASES["item"])))
    col = cols.get("expert") or cols.get("label") or cols.get("score")
    if not col:
        fail("--gold: no expert, label or score column in %s (columns: %s)" % (path, ", ".join(sorted(keys))))
    gold, warnings = {}, []
    for r in rows:
        item, e = r.get(cols["item"], ""), r.get(col, "")
        if threshold is not None and to_float(e) is not None:
            e = "pass" if to_float(e) >= threshold else "fail"
        e = norm_label(e)
        if not item or not e:
            continue
        if item in gold and gold[item] != e:
            warnings.append("gold item %s has conflicting labels (%s, %s); kept the first" % (item, gold[item], e))
            continue
        gold[item] = e
    if not gold:
        fail("--gold: no labelled items in " + str(path))
    return gold, warnings


def merge_case(recs, expert):
    """'VIOLATION' in one file and 'violation' in another are one label."""
    labels = {r["label"] for r in recs} | set(expert.values())
    spell = defaultdict(set)
    for l in labels:
        spell[l.lower()].add(l)
    if not any(len(v) > 1 for v in spell.values()):
        return
    for r in recs:
        r["label"] = r["label"].lower()
        if r["first"]:
            r["first"] = r["first"].lower()
    for i in expert:
        expert[i] = expert[i].lower()


def fill_rec(rec, r, cols):
    if "position" in cols:
        pos = (r.get(cols["position"], "") or "").strip().lower()
        rec["position"] = "first" if pos in FIRST else "second" if pos in SECOND else None
    if "first_shown" in cols:
        rec["first"] = norm_label(r.get(cols["first_shown"], "")) or None
    if "length" in cols:
        rec["length"] = to_float(r.get(cols["length"], ""))
    if "other_length" in cols:
        rec["other_length"] = to_float(r.get(cols["other_length"], ""))


# ---------- statistics ----------

def mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else None


def wilson(k, n):
    if n == 0:
        return None
    p = k / n
    d = 1 + Z * Z / n
    c = (p + Z * Z / (2 * n)) / d
    h = Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n)) / d
    return [max(0.0, c - h), min(1.0, c + h)]


def cohen(pairs):
    """Cohen's kappa for a list of (a, b) labels. Returns (kappa, observed, chance)."""
    n = len(pairs)
    if n == 0:
        return None, None, None
    po = sum(a == b for a, b in pairs) / n
    ca, cb = Counter(a for a, _ in pairs), Counter(b for _, b in pairs)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    if pe >= 1:
        return None, po, pe
    return (po - pe) / (1 - pe), po, pe


def weighted_kappa(pairs, kind="quadratic"):
    """Weighted kappa on numeric (a, b) pairs: 1 - observed / expected disagreement,
    disagreement (a-b)^2 for quadratic, |a-b| for linear."""
    n = len(pairs)
    if n == 0:
        return None
    d = (lambda x, y: (x - y) ** 2) if kind == "quadratic" else (lambda x, y: abs(x - y))
    obs = sum(d(a, b) for a, b in pairs) / n
    ca, cb = Counter(a for a, _ in pairs), Counter(b for _, b in pairs)
    exp = sum(ca[x] * cb[y] * d(x, y) for x in ca for y in cb) / (n * n)
    if exp == 0:
        return None
    return 1 - obs / exp


def fleiss(table):
    """Fleiss' kappa. table: list of per-item label lists, all the same length."""
    if not table:
        return None
    m = len(table[0])
    if m < 2:
        return None
    totals = Counter()
    pbar = 0.0
    for labels in table:
        c = Counter(labels)
        totals.update(c)
        pbar += (sum(v * v for v in c.values()) - m) / (m * (m - 1))
    pbar /= len(table)
    pe = sum((v / (len(table) * m)) ** 2 for v in totals.values())
    if pe >= 1:
        return None
    return (pbar - pe) / (1 - pe)


def ranks(xs):
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    r = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        for k in range(i, j + 1):
            r[order[k]] = (i + j) / 2 + 1
        i = j + 1
    return r


def pearson(pairs):
    if len(pairs) < 3:
        return None
    x, y = [a for a, _ in pairs], [b for _, b in pairs]
    mx, my = mean(x), mean(y)
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    sx = math.sqrt(sum((a - mx) ** 2 for a in x))
    sy = math.sqrt(sum((b - my) ** 2 for b in y))
    if sx == 0 or sy == 0:
        return None
    return sxy / (sx * sy)


def spearman(pairs):
    if len(pairs) < 3:
        return None
    return pearson(list(zip(ranks([a for a, _ in pairs]), ranks([b for _, b in pairs]))))


def pct_at(vals, q):
    return vals[int(q * (len(vals) - 1))]


def boot(units, stat, reps, rng):
    """Percentile bootstrap over units (items). stat(list_of_units) -> number or None."""
    if len(units) < 2 or reps <= 0:
        return None
    vals = []
    for _ in range(reps):
        v = stat([units[rng.randrange(len(units))] for _ in units])
        if v is not None:
            vals.append(v)
    if len(vals) < reps * 0.5:
        return None
    vals.sort()
    return [pct_at(vals, 0.025), pct_at(vals, 0.975)]


def boot2(ua, ub, stat_a, stat_b, reps, rng):
    """Bootstrap interval for stat_b(ub) - stat_a(ua), resampling each group's items separately."""
    if len(ua) < 2 or len(ub) < 2 or reps <= 0:
        return None
    vals = []
    for _ in range(reps):
        a = stat_a([ua[rng.randrange(len(ua))] for _ in ua])
        b = stat_b([ub[rng.randrange(len(ub))] for _ in ub])
        if a is not None and b is not None:
            vals.append(b - a)
    if len(vals) < reps * 0.5:
        return None
    vals.sort()
    return [pct_at(vals, 0.025), pct_at(vals, 0.975)]


def positive_class(labels, forced):
    if forced:
        for l in labels:
            if l.lower() == forced.lower():
                return l
        return forced.lower()
    labs = {l for l in labels if l not in TIES}
    if len(labs) > 2:
        return None
    pos = [l for l in labs if l in POSITIVE]
    neg = [l for l in labs if l in NEGATIVE]
    if len(pos) == 1 and (len(labs) == 1 or neg):
        return pos[0]
    return None


def trial_key(r):
    x = to_float(r["trial"])
    return (0, x, "") if x is not None else (1, 0, r["trial"])


# ---------- analysis ----------

def rate(k, n):
    return {"k": k, "n": n, "rate": k / n if n else None, "ci": wilson(k, n)}


def class_metrics(pairs, pos, reps, rng):
    """Confusion against the expert on the class the decision acts on, with Wilson intervals.
    pairs: (judge_label, expert_label)."""
    tp = sum(a == pos and b == pos for a, b in pairs)
    fp = sum(a == pos and b != pos for a, b in pairs)
    fn = sum(a != pos and b == pos for a, b in pairs)
    tn = len(pairs) - tp - fp - fn
    n = len(pairs)
    flags = [(1.0 if a == pos else 0.0, 1.0 if b == pos else 0.0) for a, b in pairs]
    rb = lambda s: 100 * mean(a - b for a, b in s) if s else None
    return {"positive": pos, "tp": tp, "fp": fp, "fn": fn, "tn": tn,
            "expert_positives": tp + fn, "expert_negatives": fp + tn, "judge_positives": tp + fp,
            "precision": rate(tp, tp + fp), "recall": rate(tp, tp + fn),
            "false_positive_rate": rate(fp, fp + tn),
            "majority_baseline": max(tp + fn, fp + tn) / n if n else None,
            "majority_label": Counter(b for _, b in pairs).most_common(1)[0][0] if pairs else None,
            "rate_bias_points": rb(flags), "rate_bias_points_ci": boot(flags, rb, reps, rng)}


def agree_block(pairs, ordinal, pos, reps, rng):
    """Agreement of one judge (one run) with the expert on the items both labelled."""
    if not pairs:
        return {"n": 0}
    k, po, pe = cohen(pairs)
    hits = sum(a == b for a, b in pairs)
    r = {"n": len(pairs), "exact": hits, "accuracy": po, "accuracy_ci": wilson(hits, len(pairs)),
         "kappa": k, "chance": pe, "kappa_ci": boot(pairs, lambda s: cohen(s)[0], reps, rng)}
    if ordinal:
        npairs = [(to_float(a), to_float(b)) for a, b in pairs]
        errs = [a - b for a, b in npairs]
        r.update({"kappa_quadratic": weighted_kappa(npairs, "quadratic"),
                  "kappa_quadratic_ci": boot(npairs, lambda s: weighted_kappa(s, "quadratic"), reps, rng),
                  "bias": mean(errs), "bias_ci": boot(errs, mean, reps, rng)})
    if pos:
        r["classes"] = class_metrics(pairs, pos, reps, rng)
    return r


def analyse(recs, expert, cols, warnings, reps, seed, forced_pos, scale=None):
    rng = random.Random(seed)
    judges = sorted({r["judge"] for r in recs}, key=natural)
    by_ji = defaultdict(list)  # (judge, item) -> recs sorted by trial
    for r in recs:
        by_ji[(r["judge"], r["item"])].append(r)
    for k in by_ji:
        by_ji[k].sort(key=trial_key)
    first = {k: v[0] for k, v in by_ji.items()}
    items = sorted({r["item"] for r in recs}, key=natural)
    expert = {i: e for i, e in expert.items() if i in set(items)}
    pairwise = "position" in cols or "first_shown" in cols
    all_labels = {r["label"] for r in recs} | set(expert.values())
    pos = None if pairwise else positive_class(all_labels, forced_pos)
    numeric = all(to_float(l) is not None for l in all_labels)
    ordinal = (not pairwise and numeric and pos is None
               and len({to_float(l) for l in all_labels}) > 2)
    if scale is not None:
        ordinal = scale == "ordinal"
    binary = (not pairwise and not ordinal
              and len({l for l in all_labels if l not in TIES}) == 2)
    if binary and pos is None:
        # the class the decision acts on: the expert's minority class unless --positive names it
        c = Counter(expert.values()) if expert else Counter(r["label"] for r in recs)
        for l in all_labels:
            c.setdefault(l, 0)
        pos = sorted(((v, natural(k), k) for k, v in c.items() if k not in TIES))[0][2]
    if forced_pos and not pairwise and pos not in all_labels:
        warnings = list(warnings) + ["--positive %s matches no label (labels: %s)"
                                     % (forced_pos, ", ".join(sorted(all_labels)))]
    trials = sorted({r["trial"] for r in recs}, key=lambda t: trial_key({"trial": t}))

    out = {"rows": len(recs), "items": len(items), "judges": judges,
           "trials_max": max(len(v) for v in by_ji.values()), "trials": trials,
           "expert_items": len(expert),
           "mode": "pairwise" if pairwise else "pointwise",
           "scale": "pairwise" if pairwise else "ordinal" if ordinal else "nominal",
           "positive_label": pos, "binary": binary, "warnings": list(warnings)}

    # label distribution, and the judge's mean on every row when scores are numeric
    dist = {}
    for j in judges:
        labs = [first[(j, i)]["label"] for i in items if (j, i) in first]
        c = Counter(labs)
        n = len(labs)
        d = {"n": n, "counts": dict(sorted(c.items(), key=lambda kv: natural(kv[0]))),
             "top_share": c.most_common(1)[0][1] / n if n else None}
        if ordinal:
            d["mean_all_rows"] = mean(to_float(l) for l in labs)
        dist[j] = d
    if expert:
        c = Counter(expert.values())
        d = {"n": len(expert), "counts": dict(sorted(c.items(), key=lambda kv: natural(kv[0]))),
             "top_share": c.most_common(1)[0][1] / len(expert)}
        if ordinal:
            d["mean_all_rows"] = mean(to_float(e) for e in expert.values())
        dist["expert"] = d
    out["distribution"] = dist

    length_of = {}
    for r in recs:
        if r["length"] is not None:
            length_of.setdefault(r["item"], r["length"])
    if length_of and not pairwise:
        out["mean_length"] = mean(length_of.values())

    # test-retest
    flipped, stability = {}, {}
    for j in judges:
        multi = [i for i in items if len(by_ji.get((j, i), [])) >= 2]
        fl = [i for i in multi if len({r["label"] for r in by_ji[(j, i)]}) > 1]
        flipped[j] = set(fl)
        stability[j] = {"items_with_repeats": len(multi), "flipped": len(fl),
                        "flip_rate": len(fl) / len(multi) if multi else None,
                        "ci": wilson(len(fl), len(multi)), "flipped_items": fl}
    for j in judges:
        retest = []
        for ta, tb in zip(trials, trials[1:]):
            la = {i: r["label"] for (jj, i), v in by_ji.items() if jj == j for r in v if r["trial"] == ta}
            lb = {i: r["label"] for (jj, i), v in by_ji.items() if jj == j for r in v if r["trial"] == tb}
            both = sorted(set(la) & set(lb), key=natural)
            if not both:
                continue
            pairs = [(la[i], lb[i]) for i in both]
            k, po, pe = cohen(pairs)
            flips = [{"item": i, "run_a": la[i], "run_b": lb[i], "expert": expert.get(i)}
                     for i in both if la[i] != lb[i]]
            entry = {"runs": [ta, tb], "joined_on_item": len(both),
                     "only_in_a": len(set(la) - set(lb)), "only_in_b": len(set(lb) - set(la)),
                     "agreed": sum(a == b for a, b in pairs), "agreement": po, "chance": pe,
                     "kappa": k, "kappa_ci": boot(pairs, lambda s: cohen(s)[0], reps, rng),
                     "flips": flips}
            if pos:
                entry["positive_in_either"] = sorted([i for i in both if pos in (la[i], lb[i])], key=natural)
                entry["positive_in_both"] = sorted([i for i in both if la[i] == lb[i] == pos], key=natural)
                entry["expert_positive_flips"] = [f["item"] for f in flips if f["expert"] == pos]
                entry["expert_positive_missed_in_both"] = sorted(
                    [i for i in both if expert.get(i) == pos and la[i] != pos and lb[i] != pos], key=natural)
            retest.append(entry)
        stability[j]["retest"] = retest
    out["stability"] = stability
    unstable = set().union(*flipped.values()) if flipped else set()
    out["unstable_items"] = sorted(unstable, key=natural)

    # agreement with expert
    vs_expert = {}
    if expert:
        for j in judges:
            res = {}
            for subset, excl in (("all", set()), ("stable", flipped[j])):
                its = [i for i in items if i in expert and (j, i) in first and i not in excl]
                pairs = [(first[(j, i)]["label"], expert[i]) for i in its]
                if not pairs:
                    res[subset] = {"n": 0}
                    continue
                k, po, pe = cohen(pairs)
                hits = sum(a == b for a, b in pairs)
                r = {"n": len(pairs), "exact": hits, "accuracy": po, "accuracy_ci": wilson(hits, len(pairs)),
                     "kappa": k, "chance": pe,
                     "kappa_ci": boot(pairs, lambda s: cohen(s)[0], reps, rng)}
                if ordinal:
                    npairs = [(to_float(a), to_float(b)) for a, b in pairs]
                    errs = [a - b for a, b in npairs]
                    r.update({
                        "kappa_quadratic": weighted_kappa(npairs, "quadratic"),
                        "kappa_quadratic_ci": boot(npairs, lambda s: weighted_kappa(s, "quadratic"), reps, rng),
                        "kappa_linear": weighted_kappa(npairs, "linear"),
                        "kappa_linear_ci": boot(npairs, lambda s: weighted_kappa(s, "linear"), reps, rng),
                        "within_one": sum(abs(e) <= 1 for e in errs),
                        "judge_mean": mean(a for a, _ in npairs),
                        "expert_mean": mean(b for _, b in npairs),
                        "bias": mean(errs), "bias_ci": boot(errs, mean, reps, rng),
                        "judge_higher": sum(e > 0 for e in errs), "judge_lower": sum(e < 0 for e in errs)})
                    if length_of:
                        pts = [(length_of[i], to_float(first[(j, i)]["label"]) - to_float(expert[i]))
                               for i in its if i in length_of]
                        r["bias_vs_length"] = {"n": len(pts), "pearson": pearson(pts),
                                               "pearson_ci": boot(pts, pearson, reps, rng),
                                               "spearman": spearman(pts)}
                if subset == "all" and pos:
                    r["classes"] = class_metrics(pairs, pos, reps, rng)
                if subset == "all":
                    conf = Counter(pairs)
                    r["confusion"] = {"%s|%s" % (a, b): v
                                      for (a, b), v in sorted(conf.items(), key=lambda kv: natural(kv[0]))}
                    if pos:
                        neg_items = [(a, b) for a, b in pairs if b != pos and b not in TIES]
                        pos_items = [(a, b) for a, b in pairs if b == pos]
                        fp = sum(a == pos for a, _ in neg_items)
                        ff = sum(a != pos for a, _ in pos_items)
                        r["false_pass"] = {"k": fp, "n": len(neg_items),
                                           "rate": fp / len(neg_items) if neg_items else None,
                                           "ci": wilson(fp, len(neg_items))}
                        r["false_fail"] = {"k": ff, "n": len(pos_items),
                                           "rate": ff / len(pos_items) if pos_items else None,
                                           "ci": wilson(ff, len(pos_items))}
                        r["pass_rate_judge"] = sum(a == pos for a, _ in pairs) / len(pairs)
                        r["pass_rate_expert"] = sum(b == pos for _, b in pairs) / len(pairs)
                res[subset] = r
            if len(trials) > 1:
                res["by_trial"] = {}
                for t in trials:
                    tp_ = []
                    for i in items:
                        rs = [x for x in by_ji.get((j, i), []) if x["trial"] == t]
                        if rs and i in expert:
                            tp_.append((rs[0]["label"], expert[i]))
                    res["by_trial"][t] = agree_block(tp_, ordinal, pos, reps, rng)
            vs_expert[j] = res
    out["vs_expert"] = vs_expert

    # agreement between judges
    between = []
    for a, b in combinations(judges, 2):
        row = {"judges": [a, b]}
        for subset, excl in (("all", set()), ("stable", unstable)):
            its = [i for i in items if (a, i) in first and (b, i) in first and i not in excl]
            pairs = [(first[(a, i)]["label"], first[(b, i)]["label"]) for i in its]
            k, po, pe = cohen(pairs)
            row[subset] = {"n": len(pairs), "agreement": po, "chance": pe, "kappa": k,
                           "kappa_ci": boot(pairs, lambda s: cohen(s)[0], reps, rng)}
            if ordinal and pairs:
                npairs = [(to_float(x), to_float(y)) for x, y in pairs]
                row[subset]["kappa_quadratic"] = weighted_kappa(npairs, "quadratic")
        if len(trials) > 1:
            per_item = defaultdict(list)  # item -> [(label_a, label_b)] matched on trial
            per_trial = {}
            for t in trials:
                tp = []
                for i in items:
                    ra = [r for r in by_ji.get((a, i), []) if r["trial"] == t]
                    rb = [r for r in by_ji.get((b, i), []) if r["trial"] == t]
                    if ra and rb:
                        tp.append((ra[0]["label"], rb[0]["label"]))
                        per_item[i].append((ra[0]["label"], rb[0]["label"]))
                k, po, pe = cohen(tp)
                per_trial[t] = {"n": len(tp), "agreement": po, "kappa": k}
            units = list(per_item.values())
            flat = [p for u in units for p in u]
            k, po, pe = cohen(flat)
            row["matched_trials"] = {
                "n": len(flat), "items": len(units), "agreed": sum(x == y for x, y in flat),
                "agreement": po, "chance": pe, "kappa": k,
                "kappa_ci": boot(units, lambda s: cohen([p for u in s for p in u])[0], reps, rng),
                "per_trial": per_trial}
        if expert:
            both = [i for i in items if i in expert and (a, i) in first and (b, i) in first]
            agree = [i for i in both if first[(a, i)]["label"] == first[(b, i)]["label"]]
            wrong = [i for i in agree if first[(a, i)]["label"] != expert[i]]
            row["shared_errors"] = {"agreed_on_expert_items": len(agree), "both_wrong": len(wrong),
                                    "items": wrong}
            units = [(first[(a, i)]["label"] == expert[i], first[(b, i)]["label"] == expert[i])
                     for i in both]
            if units:
                d = lambda s: mean(1.0 * x - 1.0 * y for x, y in s)
                row["accuracy_diff_vs_expert"] = {"n": len(units), "diff": d(units),
                                                  "ci": boot(units, d, reps, rng),
                                                  "only_a_right": sum(x and not y for x, y in units),
                                                  "only_b_right": sum(y and not x for x, y in units)}
        between.append(row)
    out["between_judges"] = between

    if len(judges) >= 3:
        full = [i for i in items if all((j, i) in first for j in judges)]
        table = [[first[(j, i)]["label"] for j in judges] for i in full]
        out["fleiss"] = {"n": len(full), "raters": len(judges), "kappa": fleiss(table),
                         "kappa_ci": boot(table, fleiss, reps, rng), "basis": "first trial per judge"}
    if len(judges) >= 2 and len(trials) > 1:
        raters = [(j, t) for j in judges for t in trials]
        lab = {(r["judge"], r["trial"], r["item"]): r["label"] for r in recs}
        full = [i for i in items if all((j, t, i) in lab for j, t in raters)]
        table = [[lab[(j, t, i)] for j, t in raters] for i in full]
        if full:
            out["fleiss_all_ratings"] = {"n": len(full), "raters": len(raters), "kappa": fleiss(table),
                                         "kappa_ci": boot(table, fleiss, reps, rng),
                                         "basis": "every judge x trial rating"}

    if pairwise:
        out["pairwise"] = pairwise_stats(recs, judges, items, reps, rng)

    # length bias
    if "length" in cols:
        lb = {}
        if pairwise:
            for j in judges:
                rs = [r for r in recs if r["judge"] == j and r["label"] not in TIES
                      and r["length"] is not None and r["other_length"] is not None
                      and r["length"] != r["other_length"]]
                k = sum(r["length"] > r["other_length"] for r in rs)
                lb[j] = {"decided_with_lengths": len(rs), "chose_longer": k,
                         "rate": k / len(rs) if rs else None, "ci": wilson(k, len(rs))}
            if "other_length" not in cols:
                out["warnings"].append("pairwise length check needs an 'other_length' column")
        else:
            def num(rec_label, rec_score):
                if rec_score is not None and not pos:
                    return rec_score
                if pos:
                    return 1.0 if rec_label == pos else 0.0
                return to_float(rec_label)

            for j in judges:
                pts = [(length_of[i], num(first[(j, i)]["label"], first[(j, i)]["score"]))
                       for i in items if (j, i) in first and i in length_of]
                pts = [p for p in pts if p[1] is not None]
                entry = {"n": len(pts), "spearman": spearman(pts), "ci": boot(pts, spearman, reps, rng)}
                if expert and pos:
                    negs = [(length_of[i], 1.0 if first[(j, i)]["label"] == pos else 0.0)
                            for i in items if i in expert and expert[i] != pos
                            and (j, i) in first and i in length_of]
                    entry["within_expert_fails"] = {"n": len(negs), "spearman": spearman(negs)}
                lb[j] = entry
            if expert:
                pts = []
                for i, e in expert.items():
                    v = (1.0 if e == pos else 0.0) if pos else to_float(e)
                    if v is not None and i in length_of:
                        pts.append((length_of[i], v))
                lb["expert"] = {"n": len(pts), "spearman": spearman(pts),
                                "ci": boot(pts, spearman, reps, rng)}
        out["length"] = lb

    out["flags"] = flags_for(out)
    return out


def pairwise_stats(recs, judges, items, reps, rng):
    """Position and win statistics. Ties count as judgements no variant won."""
    variants = sorted({r["label"] for r in recs if r["label"] not in TIES}
                      | {r["first"] for r in recs if r["first"] and r["first"] not in TIES}, key=natural)
    two = len(variants) == 2

    def first_variant(r):
        if r["first"]:
            return r["first"]
        if r["position"] and two and r["label"] in variants:
            other = [v for v in variants if v != r["label"]][0]
            return r["label"] if r["position"] == "first" else other
        return None

    rows = []
    for r in recs:
        fv = first_variant(r)
        rows.append({"item": r["item"], "judge": r["judge"], "trial": r["trial"], "label": r["label"],
                     "first": fv, "tie": r["label"] in TIES})
    out = {"variants": variants, "judgements": len(rows),
           "order_known": sum(r["first"] is not None for r in rows),
           "ties": sum(r["tie"] for r in rows)}

    def by_item(rs):
        d = defaultdict(list)
        for r in rs:
            d[r["item"]].append(r)
        return list(d.values())

    def first_win_rate(units):
        rs = [r for u in units for r in u if r["first"]]
        return sum(r["label"] == r["first"] for r in rs) / len(rs) if rs else None

    def position_block(rs):
        known = [r for r in rs if r["first"]]
        units = by_item(known)
        fw = sum(r["label"] == r["first"] for r in known)
        sw = sum((not r["tie"]) and r["label"] != r["first"] for r in known)
        blk = {"judgements": len(rs), "order_known": len(known), "ties": sum(r["tie"] for r in known),
               "first_shown_won": fw, "second_shown_won": sw,
               "first_shown_win_rate": fw / len(known) if known else None,
               "first_shown_win_rate_decided": fw / (fw + sw) if fw + sw else None,
               "ci_by_item": boot(units, first_win_rate, reps, rng)}
        if two:
            per = {}
            for v in variants:
                f = [r for r in known if r["first"] == v]
                s = [r for r in known if r["first"] != v]
                wf = sum(r["label"] == v for r in f)
                ws = sum(r["label"] == v for r in s)

                def balanced(us, v=v):
                    ff = [r for u in us for r in u if r["first"] == v]
                    ss = [r for u in us for r in u if r["first"] != v]
                    if not ff or not ss:
                        return None
                    return (sum(r["label"] == v for r in ff) / len(ff)
                            + sum(r["label"] == v for r in ss) / len(ss)) / 2

                def raw(us, v=v):
                    rr = [r for u in us for r in u]
                    return sum(r["label"] == v for r in rr) / len(rr) if rr else None

                per[v] = {"shown_first": len(f), "wins_when_first": wf,
                          "win_rate_when_first": wf / len(f) if f else None,
                          "shown_second": len(s), "wins_when_second": ws,
                          "win_rate_when_second": ws / len(s) if s else None,
                          "wins": wf + ws, "raw_win_rate": (wf + ws) / len(known) if known else None,
                          "raw_ci_by_item": boot(units, raw, reps, rng),
                          "order_balanced_win_rate": balanced(units),
                          "order_balanced_ci_by_item": boot(units, balanced, reps, rng)}
            blk["by_variant"] = per
        return blk

    out["all_judges"] = position_block(rows)
    out["per_judge"] = {j: position_block([r for r in rows if r["judge"] == j]) for j in judges}

    # how order was assigned, per item
    orders = defaultdict(set)
    for r in rows:
        if r["first"]:
            orders[r["item"]].add(r["first"])
    assign = Counter()
    for i in items:
        o = orders.get(i)
        assign["unknown" if not o else "mixed" if len(o) > 1 else "always " + next(iter(o))] += 1
    out["order_by_item"] = dict(sorted(assign.items()))
    out["items_order_fixed_across_trials"] = sum(1 for i in items if len(orders.get(i, ())) == 1)
    return out


def flags_for(o):
    flags = []
    for j, res in o["vs_expert"].items():
        n = res.get("all", {}).get("n", 0)
        if n and n < SMALL_N:
            flags.append("%s vs expert: n=%d is under %d; the interval is too wide to conclude much"
                         % (j, n, SMALL_N))
        cl = res.get("all", {}).get("classes")
        if cl:
            for side, k in (("expert_positives", "recall"), ("expert_negatives", "false_positive_rate")):
                m = cl[side]
                c = cl[k]["ci"]
                if 0 < m < 20 and c:
                    flags.append("%s: the expert has only %d %s`%s` item(s), so %s rests on %d; its "
                                 "95%% interval runs %s to %s" % (
                                     j, m, "" if side == "expert_positives" else "non-",
                                     cl["positive"], k.replace("_", " "), m, pct(c[0]), pct(c[1])))
    for row in o["between_judges"]:
        n = row["all"]["n"]
        if n and n < SMALL_N:
            flags.append("%s vs %s: n=%d is under %d" % (row["judges"][0], row["judges"][1], n, SMALL_N))
    if not o["expert_items"]:
        flags.append("no expert labels: nothing here measures whether the judges are right, "
                     "only whether they are consistent")
    pw = o.get("pairwise")
    if pw:
        a = pw["all_judges"]
        c = a.get("ci_by_item")
        if c and (c[0] > 0.5 or c[1] < 0.5):
            flags.append("the first-shown output won %d of %d judgements with known order (%s); "
                         "the item-level interval excludes 50%%"
                         % (a["first_shown_won"], a["order_known"], pct(a["first_shown_win_rate"])))
        for v, b in a.get("by_variant", {}).items():
            n = b["shown_first"] + b["shown_second"]
            if n and abs(b["shown_first"] / n - 0.5) >= 0.1:
                flags.append("`%s` was shown first in %d of %d judgements, so order was not balanced; "
                             "raw win rates mix quality with position" % (v, b["shown_first"], n))
                break
        if pw["items_order_fixed_across_trials"] and o["trials_max"] > 1:
            flags.append("%d of %d items kept the same order in every judgement; on those items "
                         "repeats never swapped order, so they cannot separate position from quality"
                         % (pw["items_order_fixed_across_trials"], o["items"]))
    if o["trials_max"] < 2:
        flags.append("one trial per judge and item: stability (flip rate) was not measured")
    if o["expert_items"] and o.get("expert_raters", 1) == 1:
        flags.append("one expert label per item: there is no expert-expert baseline to compare the "
                     "judge with")
    return flags


def group_compare(groups, ordinal, reps, seed, factor=1.0):
    """Differences between groups, each against the first group, on the judge means, the expert
    means and the bias, with intervals that resample items within each group. For two-label data
    the 'scores' are 1/0 for the positive class and factor=100 gives percentage points."""
    rng = random.Random(seed + 1)
    names = list(groups)
    if len(names) < 2:
        return []
    ref = names[0]
    out = []
    for g in names[1:]:
        row = {"group": g, "reference": ref, "by_judge": {}}
        for j in groups[g]["_judges"]:
            if j not in groups[ref]["_judges"]:
                continue
            entry = {}
            if ordinal:
                ja, jb = groups[ref]["_scores"][j], groups[g]["_scores"][j]
                fm = lambda s: factor * mean(s)
                entry["judge_mean_all_rows_diff"] = (fm(jb) - fm(ja)) if ja and jb else None
                entry["judge_mean_all_rows_diff_ci"] = boot2(ja, jb, fm, fm, reps, rng)
                entry["units"] = "percentage points of the '%s' rate" % groups[ref].get("_pos") \
                    if factor != 1.0 else "score points"
                pa, pb = groups[ref]["_pairs"].get(j, []), groups[g]["_pairs"].get(j, [])
                if pa and pb:
                    ex = lambda s: factor * mean(b for _, b in s)
                    jd = lambda s: factor * mean(a for a, _ in s)
                    bi = lambda s: factor * mean(a - b for a, b in s)
                    entry["expert_mean_diff"] = ex(pb) - ex(pa)
                    entry["expert_mean_diff_ci"] = boot2(pa, pb, ex, ex, reps, rng)
                    entry["judge_mean_labelled_diff"] = jd(pb) - jd(pa)
                    entry["judge_mean_labelled_diff_ci"] = boot2(pa, pb, jd, jd, reps, rng)
                    entry["bias_diff"] = bi(pb) - bi(pa)
                    entry["bias_diff_ci"] = boot2(pa, pb, bi, bi, reps, rng)
            row["by_judge"][j] = entry
        out.append(row)
    return out


def analyse_groups(recs, expert, cols, reps, seed, forced_pos, scale, binary=False):
    names = sorted({r["group"] for r in recs}, key=natural)
    groups, raw = {}, {}
    for g in names:
        sub = [r for r in recs if r["group"] == g]
        res = analyse(sub, expert, cols, [], reps, seed, forced_pos, scale)
        groups[g] = res
        js = res["judges"]
        first = {}
        for r in sorted(sub, key=trial_key):
            first.setdefault((r["judge"], r["item"]), r)
        raw[g] = {"_judges": js, "_scores": {}, "_pairs": {}, "_pos": forced_pos}
        if scale == "ordinal" or binary:
            v = (lambda l: 1.0 if l == forced_pos else 0.0) if binary else to_float
            for j in js:
                its = sorted({i for (jj, i) in first if jj == j}, key=natural)
                raw[g]["_scores"][j] = [v(first[(j, i)]["label"]) for i in its]
                raw[g]["_pairs"][j] = [(v(first[(j, i)]["label"]), v(expert[i]))
                                       for i in its if i in expert]
    return groups, group_compare(raw, scale == "ordinal" or binary, reps, seed,
                                 100.0 if binary else 1.0)


# ---------- the user's gate ----------

GATE_METRICS = {
    "accuracy": "rate", "kappa": "num", "quadratic": "num", "precision": "rate", "recall": "rate",
    "fpr": "rate", "false_positives": "count", "false_negatives": "count", "flip_rate": "rate",
    "bias": "abs", "bias_diff": "abs",
}
GATE_ALIASES = {"diff": "bias_diff", "kappa_quadratic": "quadratic", "false_positive_rate": "fpr",
                "fp": "false_positives", "fn": "false_negatives", "flips": "flip_rate"}


def parse_gate(spec):
    s = spec.replace(" ", "").lower()
    for op in (">=", "<=", ">", "<", "="):
        if op in s:
            name, _, val = s.partition(op)
            break
    else:
        fail("--gate %s: expected METRIC>=VALUE or METRIC<=VALUE (metrics: %s)"
             % (spec, ", ".join(GATE_METRICS)))
    name = GATE_ALIASES.get(name, name)
    if name not in GATE_METRICS:
        fail("--gate %s: unknown metric '%s' (metrics: %s)" % (spec, name, ", ".join(GATE_METRICS)))
    if op == "=":
        op = "<=" if GATE_METRICS[name] == "abs" else ">="
    is_pct = val.endswith("%")
    v = to_float(val.rstrip("%"))
    if v is None:
        fail("--gate %s: '%s' is not a number" % (spec, val))
    if GATE_METRICS[name] == "rate" and (is_pct or v > 1):
        v /= 100.0
    return {"spec": spec, "metric": name, "op": op, "value": v}


def judge_gate(g, value, interval):
    """clears when the whole interval meets the criterion, fails when none of it does."""
    if value is None:
        return "not measurable"
    kind, op, v = GATE_METRICS[g["metric"]], g["op"], g["value"]
    if kind == "abs":
        x = abs(value)
        lo_hi = None
        if interval:
            lo, hi = interval
            lo_hi = (0.0 if lo <= 0 <= hi else min(abs(lo), abs(hi)), max(abs(lo), abs(hi)))
        value, interval = x, lo_hi
    meets = (lambda x: x >= v) if op == ">=" else (lambda x: x > v) if op == ">" else \
        (lambda x: x <= v) if op == "<=" else (lambda x: x < v)
    point = meets(value)
    if not interval:
        return "clears" if point else "fails"
    lo, hi = interval
    if meets(lo) and meets(hi):
        return "clears"
    if not meets(lo) and not meets(hi):
        return "fails"
    return "can't tell: the point estimate %s, the interval spans the criterion" % (
        "meets it" if point else "misses it")


def evaluate_gates(gates, o):
    res = []
    for g in gates:
        m = g["metric"]
        rows = []
        if m == "flip_rate":
            for j, st in o["stability"].items():
                if st["items_with_repeats"]:
                    rows.append((j, None, st["flip_rate"], st["ci"]))
        elif m == "bias_diff":
            for row in o.get("group_compare", []):
                for j, e in row["by_judge"].items():
                    if e.get("bias_diff") is not None:
                        rows.append((j, "%s minus %s" % (row["group"], row["reference"]),
                                     e["bias_diff"], e.get("bias_diff_ci")))
            if not o.get("group_compare"):
                res.append({"gate": g, "results": [], "note": "bias_diff needs --group-by"})
                continue
        else:
            for j, ve in o["vs_expert"].items():
                blocks = ve.get("by_trial") or {o["trials"][0]: ve.get("all", {})}
                for t, b in blocks.items():
                    c = b.get("classes", {})
                    val = ci = None
                    if m in ("accuracy", "kappa"):
                        val, ci = b.get(m), b.get(m + "_ci")
                    elif m == "quadratic":
                        val, ci = b.get("kappa_quadratic"), b.get("kappa_quadratic_ci")
                    elif m in ("precision", "recall"):
                        val, ci = c.get(m, {}).get("rate"), c.get(m, {}).get("ci")
                    elif m == "fpr":
                        val, ci = c.get("false_positive_rate", {}).get("rate"), c.get("false_positive_rate", {}).get("ci")
                    elif m == "false_positives":
                        val = c.get("fp")
                    elif m == "false_negatives":
                        val = c.get("fn")
                    elif m == "bias":
                        if "bias" in b:
                            val, ci = b["bias"], b.get("bias_ci")
                        else:
                            val, ci = c.get("rate_bias_points"), c.get("rate_bias_points_ci")
                    rows.append((j, t if len(blocks) > 1 else None, val, ci))
        res.append({"gate": g, "results": [{"judge": j, "run": t, "value": v, "ci": c,
                                            "outcome": judge_gate(g, v, c)} for j, t, v, c in rows]})
    return res


# ---------- markdown ----------

def pct(x):
    return "n/a" if x is None else "%.0f%%" % (100 * x)


def num2(x):
    return "n/a" if x is None else "%.2f" % x


def sgn(x):
    return "n/a" if x is None else "%+.2f" % x


def pts(x):
    return "n/a" if x is None else "%+.1f pts" % x


def ci(c, as_pct=False, signed=False, points=False):
    if not c:
        return ""
    if points:
        return " [%+.1f, %+.1f]" % (c[0], c[1])
    f = pct if as_pct else sgn if signed else num2
    return " [%s, %s]" % (f(c[0]), f(c[1]))


def run_name(o, t):
    n = o.get("trial_names", {}).get(t)
    return "run %s (%s)" % (t, n) if n else "trial %s" % t


def rare_section(o):
    """Per judge and per run: confusion on the class the decision acts on, precision, recall."""
    pl = o.get("positive_label")
    L = ["### Against the expert on `%s`, per judge and run" % pl, "",
         "Joined to the expert on the item id. TP = both say `%s`; FP = judge says `%s`, expert "
         "does not; FN = expert says `%s`, judge does not." % (pl, pl, pl), "",
         "| Judge | Run | n | Judge / expert say `%s` | TP | FP | FN | TN | Precision | Recall | "
         "False-positive rate | Accuracy (always-majority baseline) | Cohen's kappa |" % pl,
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for j, ve in o["vs_expert"].items():
        blocks = ve.get("by_trial") or {o["trials"][0]: ve.get("all", {})}
        for t, b in blocks.items():
            c = b.get("classes")
            if not b.get("n") or not c:
                continue
            p, r, f = c["precision"], c["recall"], c["false_positive_rate"]
            L.append("| %s | %s | %d | %s | %d | %d | %d | %d | %s%s | %s%s | %s%s | %s%s (%s) | %s%s |" % (
                j, run_name(o, t) if len(blocks) > 1 else "%s only" % run_name(o, t) if o["trials_max"] > 1 else "-",
                b["n"], "%s / %s" % (frac(c["judge_positives"], b["n"]), frac(c["expert_positives"], b["n"])),
                c["tp"], c["fp"], c["fn"], c["tn"],
                frac(p["k"], p["n"]) if p["n"] else "n/a", ci(p["ci"], True),
                frac(r["k"], r["n"]) if r["n"] else "n/a", ci(r["ci"], True),
                frac(f["k"], f["n"]) if f["n"] else "n/a", ci(f["ci"], True),
                frac(b["exact"], b["n"]), ci(b["accuracy_ci"], True),
                "always `%s`: %s" % (c["majority_label"], pct(c["majority_baseline"])),
                num2(b["kappa"]), ci(b["kappa_ci"])))
    L.append("")
    return L


def retest_section(o):
    pl = o.get("positive_label")
    L = ["### Run against run (joined on item id)", "",
         "| Judge | Runs | Items in both | Only in one | Same label | Chance | Cohen's kappa | Flipped |",
         "|---|---|---|---|---|---|---|---|"]
    notes = []
    for j, st in o["stability"].items():
        for e in st.get("retest", []):
            a, b = e["runs"]
            L.append("| %s | %s vs %s | %d | %d / %d | %s | %s | %s%s | %d |" % (
                j, a, b, e["joined_on_item"], e["only_in_a"], e["only_in_b"],
                frac(e["agreed"], e["joined_on_item"]), pct(e["chance"]), num2(e["kappa"]),
                ci(e["kappa_ci"]), len(e["flips"])))
            fl = ", ".join("%s (%s → %s%s)" % (f["item"], f["run_a"], f["run_b"],
                                                ", expert " + (f["expert"] or "unlabelled") if o["expert_items"] else "")
                           for f in e["flips"][:25]) + (" …" if len(e["flips"]) > 25 else "")
            notes.append("- **%s**, run %s → run %s flips: %s" % (j, a, b, fl or "none"))
            if pl and "positive_in_either" in e:
                ids = lambda xs: (" (%s)" % ", ".join(xs)) if 0 < len(xs) <= 25 else ""
                line = "  - `%s` in either run: %d%s; in both runs: %d%s." % (
                    pl, len(e["positive_in_either"]), ids(e["positive_in_either"]),
                    len(e["positive_in_both"]), ids(e["positive_in_both"]))
                if o["expert_items"]:
                    line += " Expert-`%s` items that flipped: %s. Expert-`%s` items missed in both runs: %s." % (
                        pl, ", ".join(e["expert_positive_flips"]) or "none",
                        pl, ", ".join(e["expert_positive_missed_in_both"]) or "none")
                notes.append(line)
    return L + [""] + notes + [""]


def gate_section(o):
    L = ["## Against the stated criterion", ""]
    for gr in o["gates"]:
        g = gr["gate"]
        if gr.get("note"):
            L.append("- `%s`: %s" % (g["spec"], gr["note"]))
            continue
        if not gr["results"]:
            L.append("- `%s`: not measurable on this data" % g["spec"])
        for r in gr["results"]:
            kind = GATE_METRICS[g["metric"]]
            v, c = r["value"], r["ci"]
            shown = "n/a" if v is None else pct(v) if kind == "rate" else \
                str(v) if kind == "count" else "%+.2f" % v
            cshown = ci(c, as_pct=True) if kind == "rate" else ci(c, signed=True) if c else ""
            L.append("- `%s` · %s%s: %s%s → **%s**" % (
                g["spec"], r["judge"], (", " + (run_name(o, r["run"]) if g["metric"] != "bias_diff"
                                               else r["run"])) if r["run"] else "",
                shown, cshown, r["outcome"]))
    L.append("")
    return L


def frac(k, n):
    return "%d/%d (%s)" % (k, n, pct(k / n if n else None))


def group_section(o, col):
    groups = o["groups"]
    names = list(groups)
    L = ["## By %s (the comparison the decision makes)" % col, ""]
    first = groups[names[0]]
    if first["mode"] == "pairwise":
        L += ["| %s | Judge | Judgements | First-shown won | Order-balanced win rate | Flip rate |" % col,
              "|---|---|---|---|---|---|"]
        for g in names:
            pw = groups[g]["pairwise"]
            blocks = list(pw["per_judge"].items())
            if len(blocks) > 1:
                blocks = [("all judges", pw["all_judges"])] + blocks
            for j, b in blocks:
                bal = "; ".join("%s %s%s" % (v, pct(x["order_balanced_win_rate"]),
                                              ci(x["order_balanced_ci_by_item"], True))
                                for v, x in b.get("by_variant", {}).items())
                st = groups[g]["stability"].get(j)
                flip = ("%d/%d" % (st["flipped"], st["items_with_repeats"])) if st and st["items_with_repeats"] else "n/a"
                L.append("| %s | %s | %d | %s | %s | %s |"
                         % (g, j, b["judgements"], frac(b["first_shown_won"], b["order_known"]),
                            bal or "n/a", flip))
        L.append("")
        return L

    ordinal = any(groups[g]["scale"] == "ordinal" for g in names)
    for j in o["judges"]:
        rows = []
        for g in names:
            res = groups[g]
            r = res["vs_expert"].get(j, {}).get("all", {})
            d = res["distribution"].get(j, {})
            if not d.get("n"):
                continue
            ln = res.get("mean_length")
            if ordinal:
                bl = r.get("bias_vs_length", {})
                rows.append("| %s | %d | %s | %d | %s | %s | %s | %s | %s%s | %s%s | %s / %s | %s | %s |" % (
                    g, d.get("n", 0), num2(d.get("mean_all_rows")), r.get("n", 0),
                    num2(r.get("judge_mean")), num2(r.get("expert_mean")),
                    frac(r["exact"], r["n"]) if r.get("n") else "n/a",
                    frac(r["within_one"], r["n"]) if r.get("n") else "n/a",
                    num2(r.get("kappa_quadratic")), ci(r.get("kappa_quadratic_ci")),
                    sgn(r.get("bias")), ci(r.get("bias_ci"), signed=True),
                    r.get("judge_higher", "n/a"), r.get("judge_lower", "n/a"),
                    "n/a" if ln is None else "%.0f" % ln, num2(bl.get("pearson"))))
            else:
                c = r.get("classes")
                pl = o.get("positive_label")
                jr = d.get("counts", {}).get(pl, 0) if pl else None
                rows.append("| %s | %d | %s | %d | %s | %s%s | %s | %s | %s%s |" % (
                    g, d.get("n", 0), frac(jr, d["n"]) if jr is not None else "n/a", r.get("n", 0),
                    frac(r["exact"], r["n"]) if r.get("n") else "n/a",
                    num2(r.get("kappa")), ci(r.get("kappa_ci")),
                    "%d/%d/%d/%d" % (c["tp"], c["fp"], c["fn"], c["tn"]) if c else "n/a",
                    "%d/%d" % (c["fp"], c["expert_negatives"]) if c else "n/a",
                    pts(c["rate_bias_points"]) if c else "n/a",
                    ci(c["rate_bias_points_ci"], points=True) if c else ""))
        L.append("**%s**" % j)
        L.append("")
        if ordinal:
            L += ["| %s | Rows | Judge mean, all rows | Expert-labelled | Judge mean, labelled | "
                  "Expert mean, labelled | Exact agreement | Within 1 | Quadratic kappa | "
                  "Bias judge-expert | Judge higher / lower | Mean length | Bias vs length r |" % col,
                  "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
        else:
            pl = o.get("positive_label")
            L += ["| %s | Rows | Judge says `%s`, all rows | Expert-labelled | Exact agreement | "
                  "Cohen's kappa | TP/FP/FN/TN on `%s` | Judge `%s` where expert not | "
                  "`%s` rate bias judge-expert |" % (col, pl, pl, pl, pl),
                  "|---|---|---|---|---|---|---|---|---|"]
        L += rows + [""]
    for row in o.get("group_compare", []):
        for j, e in row["by_judge"].items():
            if not e:
                continue
            what = "mean" if e.get("units", "score points") == "score points" else \
                "'%s' rate, in percentage points," % o.get("positive_label")
            L.append(("- **%s minus %s**, %s: judge " + what + " on all rows %s%s; on expert-labelled rows "
                      "judge %s%s, expert %s%s; bias (judge-expert) differs by %s%s.")
                     % (row["group"], row["reference"], j,
                        sgn(e.get("judge_mean_all_rows_diff")), ci(e.get("judge_mean_all_rows_diff_ci"), signed=True),
                        sgn(e.get("judge_mean_labelled_diff")), ci(e.get("judge_mean_labelled_diff_ci"), signed=True),
                        sgn(e.get("expert_mean_diff")), ci(e.get("expert_mean_diff_ci"), signed=True),
                        sgn(e.get("bias_diff")), ci(e.get("bias_diff_ci"), signed=True)))
    L.append("")
    return L


def markdown(o, source):
    L = ["# Judge statistics", "",
         "Source: `%s` · %d judgements · %d items · judges: %s · up to %d trial(s) · "
         "expert-labelled items: %d · mode: %s · scale: %s"
         % (source, o["rows"], o["items"], ", ".join(o["judges"]), o["trials_max"],
            o["expert_items"], o["mode"], o["scale"]),
         "", "Intervals are 95%: Wilson for single rates, percentile bootstrap over items for kappa, "
         "means, differences, correlations and every pairwise rate. Every comparison joins on the "
         "item id." + (" Where a table does not say which run, agreement with the expert uses each "
                       "judge's first trial per item." if o["trials_max"] > 1 else ""), ""]
    if o.get("trial_names"):
        L += ["Runs: " + "; ".join(run_name(o, t) for t in o["trials"]), ""]
    if o["flags"]:
        L += ["## Flags", ""] + ["- " + f for f in o["flags"]] + [""]
    if o.get("gates"):
        L += gate_section(o)
    if o.get("binary") and o["vs_expert"]:
        L += rare_section(o)
    if o["trials_max"] > 1 and any(s_.get("retest") for s_ in o["stability"].values()):
        L += retest_section(o)
    if "groups" in o:
        L += group_section(o, o["group_by"])
        L += ["## Pooled across every %s" % o["group_by"], ""]

    L += ["### Label distribution (first trial)", "", "| Rater | n | Counts | Most common share | Mean |",
          "|---|---|---|---|---|"]
    for r, d in o["distribution"].items():
        counts = ", ".join("%s %d" % (k, v) for k, v in d["counts"].items())
        L.append("| %s | %d | %s | %s | %s |" % (r, d["n"], counts, pct(d["top_share"]),
                                                num2(d.get("mean_all_rows"))))
    L.append("")

    if o["vs_expert"]:
        L += ["### Agreement with expert labels", ""]
        if o["scale"] == "ordinal":
            L += ["| Judge | Subset | n | Exact | Within 1 | Cohen's kappa (unweighted) | Quadratic kappa | "
                  "Linear kappa | Judge mean | Expert mean | Bias judge-expert | Higher / lower |",
                  "|---|---|---|---|---|---|---|---|---|---|---|---|"]
        else:
            L += ["| Judge | Subset | n | Accuracy | Chance | Cohen's kappa |", "|---|---|---|---|---|---|"]
        for j, res in o["vs_expert"].items():
            for sub in ("all", "stable"):
                r = res.get(sub, {})
                if not r.get("n") or (sub == "stable" and o["trials_max"] < 2):
                    continue
                multi = o["trials_max"] > 1
                label = ("first trial only" if multi else "all labelled") if sub == "all" \
                    else "stable across trials"
                if o["scale"] == "ordinal":
                    L.append("| %s | %s | %d | %s | %s | %s%s | %s%s | %s%s | %s | %s | %s%s | %d / %d |"
                             % (j, label, r["n"], frac(r["exact"], r["n"]), frac(r["within_one"], r["n"]),
                                num2(r["kappa"]), ci(r["kappa_ci"]),
                                num2(r["kappa_quadratic"]), ci(r["kappa_quadratic_ci"]),
                                num2(r["kappa_linear"]), ci(r["kappa_linear_ci"]),
                                num2(r["judge_mean"]), num2(r["expert_mean"]),
                                sgn(r["bias"]), ci(r["bias_ci"], signed=True),
                                r["judge_higher"], r["judge_lower"]))
                else:
                    L.append("| %s | %s | %d | %s%s | %s | %s%s |"
                             % (j, label, r["n"], pct(r["accuracy"]), ci(r["accuracy_ci"], True),
                                pct(r["chance"]), num2(r["kappa"]), ci(r["kappa_ci"])))
        L.append("")
        for j, res in o["vs_expert"].items():
            r = res.get("all", {})
            if not r.get("n") or r.get("classes"):
                continue
            conf = ", ".join("judge %s / expert %s: %d" % tuple(k.split("|") + [v])
                             for k, v in r["confusion"].items())
            L.append("- **%s** confusion: %s" % (j, conf))
            if "false_pass" in r:
                fp, ff = r["false_pass"], r["false_fail"]
                L.append("  - passes %d of %d items the expert failed (%s%s); fails %d of %d the expert "
                         "passed (%s%s). Pass rate on these items: judge %s, expert %s."
                         % (fp["k"], fp["n"], pct(fp["rate"]), ci(fp["ci"], True), ff["k"], ff["n"],
                            pct(ff["rate"]), ci(ff["ci"], True), pct(r["pass_rate_judge"]),
                            pct(r["pass_rate_expert"])))
            bl = r.get("bias_vs_length")
            if bl and bl["n"]:
                L.append("  - bias (judge-expert) vs length on %d labelled items: Pearson r %s%s, "
                         "Spearman %s." % (bl["n"], num2(bl["pearson"]), ci(bl["pearson_ci"]),
                                           num2(bl["spearman"])))
        L.append("")

    if o["between_judges"]:
        L += ["### Agreement between judges", "",
              "| Pair | Basis | n | Raw agreement | Chance | Cohen's kappa |", "|---|---|---|---|---|---|"]
        for row in o["between_judges"]:
            pair = "%s vs %s" % tuple(row["judges"])
            for sub in ("all", "stable"):
                r = row[sub]
                if not r["n"] or (sub == "stable" and o["trials_max"] < 2):
                    continue
                L.append("| %s | %s | %d | %s | %s | %s%s |"
                         % (pair, "first trial" if sub == "all" else "first trial, stable items",
                            r["n"], pct(r["agreement"]), pct(r["chance"]), num2(r["kappa"]), ci(r["kappa_ci"])))
            m = row.get("matched_trials")
            if m:
                L.append("| %s | every trial, matched by trial | %d (%d items) | %d/%d (%s) | %s | %s%s |"
                         % (pair, m["n"], m["items"], m["agreed"], m["n"], pct(m["agreement"]),
                            pct(m["chance"]), num2(m["kappa"]), ci(m["kappa_ci"])))
                for t, pt in m["per_trial"].items():
                    L.append("| %s | trial %s only | %d | %s | | %s |"
                             % (pair, t, pt["n"], pct(pt["agreement"]), num2(pt["kappa"])))
        L.append("")
        for row in o["between_judges"]:
            se = row.get("shared_errors")
            if se:
                L.append("- %s and %s agree on %d expert-labelled items; on %d of them both are wrong%s."
                         % (row["judges"][0], row["judges"][1], se["agreed_on_expert_items"],
                            se["both_wrong"], (" (" + ", ".join(se["items"]) + ")") if se["items"] else ""))
        for row in o["between_judges"]:
            ad = row.get("accuracy_diff_vs_expert")
            if ad:
                L.append("- accuracy vs expert, %s minus %s on the same %d items: %s points%s "
                         "(only %s right on %d, only %s right on %d)."
                         % (row["judges"][0], row["judges"][1], ad["n"], "%+.1f" % (100 * ad["diff"]),
                            ci([100 * x for x in ad["ci"]], points=True) if ad["ci"] else "",
                            row["judges"][0], ad["only_a_right"], row["judges"][1], ad["only_b_right"]))
        if any(row.get("shared_errors") for row in o["between_judges"]):
            L.append("")
    for key in ("fleiss", "fleiss_all_ratings"):
        if key in o:
            f = o[key]
            L += ["**Fleiss' kappa** (%s), %d raters on %d items: %s%s"
                  % (f["basis"], f["raters"], f["n"], num2(f["kappa"]), ci(f["kappa_ci"])), ""]

    if o["trials_max"] > 1:
        L += ["### Test-retest stability", "",
              "| Judge | Items with repeats | Flipped | Flip rate | Flipped items |", "|---|---|---|---|---|"]
        for j, s in o["stability"].items():
            its = s["flipped_items"]
            shown = ", ".join(its[:20]) + (" …" if len(its) > 20 else "")
            L.append("| %s | %d | %d | %s%s | %s |" % (j, s["items_with_repeats"], s["flipped"],
                                                       pct(s["flip_rate"]), ci(s["ci"], True), shown or "none"))
        L.append("")

    pw = o.get("pairwise")
    if pw:
        L += ["### Position (pairwise)", "",
              "Order assignment per item: " + ", ".join("%s %d" % kv for kv in pw["order_by_item"].items())
              + ". Ties count as judgements no variant won.", "",
              "| Judge | Judgements with known order | First shown won | Second shown won | Ties |",
              "|---|---|---|---|---|"]
        for j, b in [("all judges", pw["all_judges"])] + list(pw["per_judge"].items()):
            L.append("| %s | %d | %s%s | %d | %d |"
                     % (j, b["order_known"], frac(b["first_shown_won"], b["order_known"]),
                        ci(b["ci_by_item"], True), b["second_shown_won"], b["ties"]))
        L.append("")
        for j, b in [("all judges", pw["all_judges"])] + list(pw["per_judge"].items()):
            for v, x in b.get("by_variant", {}).items():
                L.append("- **%s**, `%s`: shown first %d, won %s; shown second %d, won %s. Raw win rate "
                         "%s%s; order-balanced %s%s (intervals bootstrapped over items)."
                         % (j, v, x["shown_first"], frac(x["wins_when_first"], x["shown_first"]),
                            x["shown_second"], frac(x["wins_when_second"], x["shown_second"]),
                            pct(x["raw_win_rate"]), ci(x["raw_ci_by_item"], True),
                            pct(x["order_balanced_win_rate"]), ci(x["order_balanced_ci_by_item"], True)))
        L.append("")

    if "length" in o:
        L += ["### Length", ""]
        if o["mode"] == "pairwise":
            for j, e in o["length"].items():
                L.append("- **%s** chose the longer output in %d of %d decided pairs (%s%s)."
                         % (j, e["chose_longer"], e["decided_with_lengths"], pct(e["rate"]), ci(e["ci"], True)))
        else:
            L += ["| Rater | n | Spearman (score or pass vs length) |", "|---|---|---|"]
            for r, e in o["length"].items():
                L.append("| %s | %d | %s%s |" % (r, e["n"], num2(e["spearman"]), ci(e.get("ci"))))
            within = [(r, e["within_expert_fails"]) for r, e in o["length"].items()
                      if e.get("within_expert_fails", {}).get("n")]
            if within:
                L.append("")
            for r, w in within:
                L.append("- **%s**, items the expert failed only (n=%d): Spearman pass vs length %s."
                         % (r, w["n"], num2(w["spearman"])))
        L.append("")

    if o["warnings"]:
        L += ["## Input warnings", ""] + ["- " + w for w in o["warnings"][:30]] + [""]
    return "\n".join(L)


# ---------- self-test ----------

def self_test():
    """Check the statistics against tables worked out by hand (see reference.md)."""
    ok = True

    def check(name, got, want, tol=1e-9):
        nonlocal ok
        good = got is not None and abs(got - want) <= tol
        ok = ok and good
        sys.stdout.write("%s %s: got %s, want %s\n" % ("ok  " if good else "FAIL", name, got, want))

    # 10 items on a 1-3 scale: (1,1)x2 (2,2)x3 (3,3)x2 (1,2) (2,3) (3,1).
    t = [(1, 1)] * 2 + [(2, 2)] * 3 + [(3, 3)] * 2 + [(1, 2), (2, 3), (3, 1)]
    # quadratic: observed (1+1+4)/10 = 0.6; expected 1.2 from marginals .3/.4/.3 each; 1 - 0.6/1.2
    check("quadratic kappa", weighted_kappa(t, "quadratic"), 0.5)
    # linear: observed (1+1+2)/10 = 0.4; expected 0.84; 1 - 0.4/0.84 = 11/21
    check("linear kappa", weighted_kappa(t, "linear"), 11 / 21)
    # unweighted: po 0.7, pe 0.34, (0.7-0.34)/0.66 = 6/11
    check("unweighted kappa", cohen(t)[0], 6 / 11)
    check("mean bias", mean(a - b for a, b in t), 0.0)
    # reference.md worked example: 50 items, kappa 0.40
    t2 = [("yes", "yes")] * 20 + [("no", "no")] * 15 + [("yes", "no")] * 5 + [("no", "yes")] * 10
    check("cohen kappa (reference.md)", cohen(t2)[0], 0.4)
    # binary data: weighted and unweighted kappa coincide
    tb = [(1, 1)] * 20 + [(0, 0)] * 15 + [(1, 0)] * 5 + [(0, 1)] * 10
    check("quadratic = unweighted on binary", weighted_kappa(tb, "quadratic"), 0.4)
    # Fleiss on 3 items x 2 raters equals Scott's pi: labels a/a, a/b, b/b -> pbar 2/3, pe 0.5
    check("fleiss kappa", fleiss([["a", "a"], ["a", "b"], ["b", "b"]]), 1 / 3)
    check("pearson", pearson([(1, 2), (2, 4), (3, 6), (4, 8)]), 1.0)
    # rare class: 100 items, 5 expert positives; judge flags 4, 3 of them right
    t3 = [("v", "v")] * 3 + [("v", "o")] + [("o", "v")] * 2 + [("o", "o")] * 94
    cm = class_metrics(t3, "v", 0, random.Random(1))
    check("precision 3/4", cm["precision"]["rate"], 0.75)
    check("recall 3/5", cm["recall"]["rate"], 0.6)
    check("false-positive rate 1/95", cm["false_positive_rate"]["rate"], 1 / 95)
    check("majority baseline 95/100", cm["majority_baseline"], 0.95)
    # Wilson 3/5: centre (0.6 + 1.92/5) / 1.768 = 0.557, half 0.326 -> [0.231, 0.882]
    check("wilson 3/5 lower", wilson(3, 5)[0], 0.2307, 1e-3)
    g = parse_gate("recall>=90%")
    check("gate parses 90% as 0.9", g["value"], 0.9)
    check("gate fails when the whole interval is below", 1.0 if judge_gate(g, 0.6, [0.23, 0.88]) == "fails" else 0.0, 1.0)
    check("gate can't tell when the interval spans", 1.0 if judge_gate(g, 0.95, [0.8, 0.99]).startswith("can't") else 0.0, 1.0)
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description="Agreement, stability and bias statistics for LLM judges.")
    ap.add_argument("inputs", nargs="*", metavar="input",
                    help="CSV or JSONL of judgements, or - for stdin; several files = one run each, "
                         "joined on the item id")
    ap.add_argument("--gold", help="expert labels in their own file, joined on the item id")
    ap.add_argument("--judges", help="wide file: comma-separated columns, one per judge, each holding "
                                     "that judge's label for the row's item")
    ap.add_argument("--map", action="append", default=[], metavar="FROM=TO[,FROM=TO]",
                    help="rename labels before anything is compared, e.g. true=violation,false=ok")
    ap.add_argument("--gate", action="append", default=[], metavar="SPEC",
                    help="the user's own criterion, e.g. 'recall>=0.9', 'bias_diff<=1.0', "
                         "'false_positives<=0' (only a criterion the user stated)")
    ap.add_argument("-o", "--output", help="write the report here instead of stdout")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of markdown")
    ap.add_argument("--threshold", type=float,
                    help="score at or above this counts as pass (only a threshold the user stated)")
    ap.add_argument("--positive", help="the class the decision acts on or counts (pass, violation, "
                                       "relevant); default: pass/yes/good when present, else the "
                                       "expert's minority class")
    ap.add_argument("--expert-judge", help="treat this judge id's rows as the expert labels")
    ap.add_argument("--group-by", help="stratify every statistic by this column (version, arm, judge, ...)")
    ap.add_argument("--col", action="append", default=[], metavar="NAME=COLUMN",
                    help="map a column, e.g. --col score=grader_points (repeatable)")
    ap.add_argument("--boot", type=int, default=2000, help="bootstrap resamples (default 2000)")
    ap.add_argument("--seed", type=int, default=7, help="bootstrap seed (default 7)")
    ap.add_argument("--self-test", action="store_true", help="check the maths on hand-computed tables")
    a = ap.parse_args()
    if a.self_test:
        sys.exit(self_test())
    if not a.inputs:
        ap.error("an input file (or -) is required")
    if len(a.inputs) > 1 and "-" in a.inputs:
        fail("stdin (-) can only be the single input")
    overrides = {}
    for spec in a.col:
        name, sep, col = spec.partition("=")
        if not sep or name.strip().lower() not in ALIASES or not col.strip():
            fail("--col expects NAME=COLUMN with NAME one of: " + ", ".join(ALIASES))
        overrides[name.strip().lower()] = col.strip().lower()
    for spec in a.map:
        for part in spec.split(","):
            frm, sep, to = part.partition("=")
            if not sep or not frm.strip() or not to.strip():
                fail("--map expects FROM=TO[,FROM=TO], got " + spec)
            LABEL_MAP[frm.strip().lower()] = to.strip()
    gates = [parse_gate(g) for g in a.gate]
    wide = [c.strip().lower() for c in a.judges.split(",") if c.strip()] if a.judges else None

    multi = len(a.inputs) > 1
    used = set() if multi else None
    recs, expert, cols, warnings, orders, names = [], {}, {}, [], {}, {}
    for idx, path in enumerate(a.inputs, 1):
        t = str(idx) if multi else None
        r, e, c, w, order = load(path, a.threshold, a.expert_judge, a.group_by, overrides,
                                 trial_override=t, wide=wide, used=used)
        recs += r
        warnings += w
        for k, v in c.items():
            cols.setdefault(k, v)
        for i, lab in e.items():
            if i in expert and expert[i] != lab:
                warnings.append("item %s: expert label %s in %s conflicts with %s; kept the first"
                                % (i, lab, Path(path).name, expert[i]))
            else:
                expert.setdefault(i, lab)
        if multi:
            orders[t], names[t] = order, Path(path).name
    if multi:
        missing = set(overrides) - used
        if missing:
            fail("--col %s: no such column in any input" % ", ".join(sorted(missing)))
        ts = sorted(orders, key=int)
        base = orders[ts[0]]
        for t in ts[1:]:
            common = set(base) & set(orders[t])
            if [i for i in base if i in common] != [i for i in orders[t] if i in common]:
                warnings.append("%s lists the items in a different order from %s; every comparison "
                                "here joins on the item id, so line order plays no part"
                                % (names[t], names[ts[0]]))
            if set(base) != set(orders[t]):
                warnings.append("%s and %s cover different items (%d only in the first, %d only in the "
                                "second); run-against-run figures use the items in both"
                                % (names[ts[0]], names[t], len(set(base) - set(orders[t])),
                                   len(set(orders[t]) - set(base))))
    if a.gold:
        gold, w = load_gold(a.gold, a.threshold, overrides)
        warnings += w
        for i, lab in gold.items():
            if i in expert and expert[i] != lab:
                warnings.append("item %s: --gold says %s, the judgement file says %s; used --gold"
                                % (i, lab, expert[i]))
            expert[i] = lab
        judged = {r["item"] for r in recs}
        if not set(gold) & judged:
            fail("--gold: none of its item ids match the judgement files (first gold ids: %s; first "
                 "judged: %s)" % (", ".join(sorted(gold)[:3]), ", ".join(sorted(judged)[:3])))
        if set(gold) - judged:
            warnings.append("%d gold items were never judged" % len(set(gold) - judged))
    merge_case(recs, expert)
    labels_by_trial = defaultdict(set)
    for r in recs:
        labels_by_trial[r["trial"]].add(r["label"])
    ev = set(expert.values())
    label_flags = []
    for t, labs in labels_by_trial.items():
        if ev and not (labs & ev):
            label_flags.append("the judge labels%s (%s) share no value with the expert labels (%s); "
                            "rename them with --map before reading any agreement figure"
                            % (" in " + names[t] if t in names else "", ", ".join(sorted(labs)),
                               ", ".join(sorted(ev))))

    result = analyse(recs, expert, cols, warnings, a.boot, a.seed, a.positive)
    result["flags"] = label_flags + result["flags"]
    if names:
        result["trial_names"] = names
    if a.group_by:
        result["group_by"] = a.group_by
        result["groups"], result["group_compare"] = analyse_groups(
            recs, expert, cols, a.boot, a.seed, result["positive_label"] if result["binary"] else a.positive,
            result["scale"], result["binary"])
    if gates:
        result["gates"] = evaluate_gates(gates, result)
    src = "stdin" if a.inputs == ["-"] else ", ".join(Path(p).name for p in a.inputs)
    if a.gold:
        src += " + gold " + Path(a.gold).name
    text = json.dumps(result, indent=2) if a.json else markdown(result, src)
    if a.output:
        with open(a.output, "w", encoding="utf-8") as f:
            f.write(text + "\n")
    else:
        sys.stdout.write(text + "\n")


if __name__ == "__main__":
    main()

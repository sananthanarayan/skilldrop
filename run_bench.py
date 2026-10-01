#!/usr/bin/env python3
"""Measure what a skill is worth: the same request with the skill and without it.

run_evals.py asks "does the skill's output meet its assertions?". This asks the question that
number can't answer alone: "compared to what, and at what cost?". For every eval in a skill's
evals/evals.json it runs a paired comparison on each model:

  skill     SKILL.md is the system prompt (what run_evals.py does)
  baseline  the same request with no skill, only a one-line agent prompt
  floor     a non-answer, graded like any output. Shows how many assertions pass vacuously
            ("does not invent rows"), so the other two numbers have a zero to stand on.

Two measures, because the assertions were written by the skill's author:

  assertions  a judge checks each output against the eval's assertions. It never sees which
              arm produced the output.
  pairwise    a judge sees the request and both outputs in a shuffled order, with no
              assertions and no skill text, and picks the one that serves the request better.

Every call's tokens come from the API's usage block and are priced at that model's rate, with
the judge's spend kept apart from the generation's. Reported per model: pass rate per arm, the
paired lift with a 95% bootstrap interval over evals, the pairwise win rate, and cost per run.
With more than one model it also shows, per skill, the cheapest model that scores within
--tolerance of the best next to the tier model-routing.json assigns.

Two backends:

  api         one Messages API call per arm, no tools. Needs ANTHROPIC_API_KEY. Only sound for
              a skill whose work is all in the reply: with no tools a model that wants to read
              a file or run a script says so and stops, and both arms score near zero.
  claude-cli  a real agent run per arm through a signed-in Claude Code (`claude -p`): its own
              system prompt, file and shell tools, an empty working directory, the OS sandbox
              (no writes outside the directory, no network), and no settings, plugins or MCP
              servers from this machine. The skill arm gets the skill's folder at
              skills/<name>/; the baseline is plain Claude Code. Graded on the final message
              plus the files left behind. No API key; dollars are list price for the tokens.

An eval whose prompt names input files keeps them in evals/files/<eval id>/. They are copied
into the working directory for both arms (claude-cli only).

Spending is capped: --budget is a hard stop (default $5), --dry-run prints the call count and a
rough estimate and spends nothing, and every response is cached under .bench-cache/ so a rerun
or a resumed run pays only for what is new.

  python3 run_bench.py --dry-run
  python3 run_bench.py --backend claude-cli --skills md-to-xlsx,adr-generator --trials 3
  python3 run_bench.py --backend claude-cli --budget 60 --publish docs/benchmarks/latest.json

Limits to keep in mind when reading the numbers: one or two evals per skill, so a per-skill
number is an anecdote and the catalogue-wide number is the result; the skill's author wrote
the assertions; the judge is a model too.
"""
import argparse
import hashlib
import json
import os
import random
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import catalog
from anthropic_api import APIError, api_key, messages
from run_evals import grade, load, skill_system

ROOT = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(ROOT, ".bench-cache")
JUDGE_MODEL = "claude-sonnet-5-5"

# USD per million tokens (input, output), Anthropic first-party rates as of 2026-09-25.
# A cache read bills at 0.1x input and a cache write at 1.25x input.
PRICES = {
    "claude-haiku-4-5": (1.0, 5.0),
    "claude-sonnet-5": (2.0, 10.0),
    "claude-sonnet-5-5": (2.0, 10.0),
    "claude-opus-5": (5.0, 25.0),
    "claude-opus-5-5": (4.0, 20.0),
}

BASELINE_SYSTEM = ("You are an AI coding agent helping a user with a request.\n\n---\nThis is a "
                   "non-interactive run: the user cannot answer follow-up questions. Work with what "
                   "the request gives you.")
FLOOR_OUTPUT = "I can't help with that."
PAIR_SYSTEM = ("You compare two responses to the same request. Pick the one that would better serve "
               "the person who asked: correct, complete for what was asked, and usable as it stands. "
               "Do not reward length, confidence or formatting for their own sake. Reply with JSON "
               "only: {\"winner\": \"A\" | \"B\" | \"tie\", \"why\": \"<one short sentence>\"}")


BACKEND = "api"  # or "claude-cli"; set from --backend


CLI_BASE = ["--disable-slash-commands", "--strict-mcp-config", "--no-session-persistence",
            "--output-format", "json"]
# Settings for an agent run: commands run in Claude Code's OS sandbox, which blocks writes
# outside the working directory and all network access.
CLI_SANDBOX = json.dumps({"sandbox": {"enabled": True, "autoAllowBashIfSandboxed": True}})
VIEWER = os.path.join(ROOT, "packs", "converters", "skills", "file-to-markdown", "scripts", "to_markdown.py")


def cli_run(cmd, user, cwd, timeout, env=None):
    """One `claude -p` run; returns (text, response) in the shape the API path returns, with the
    cost Claude Code reports (list price for the tokens used, cache reads included)."""
    r = {}
    for attempt in range(3):
        try:
            p = subprocess.run(["claude", "-p"] + cmd + CLI_BASE, input=user, capture_output=True, text=True,
                               cwd=cwd, timeout=timeout, env=env)
            r = json.loads(p.stdout)
        except (subprocess.TimeoutExpired, ValueError, OSError) as err:
            r = {"is_error": True, "result": str(err)[:300]}
        if not r.get("is_error"):
            used = r.get("modelUsage", {})
            served = sorted(used, key=lambda m: -used[m].get("outputTokens", 0))
            return r.get("result", ""), {"model": served[0] if served else "", "usage": r.get("usage", {}),
                                         "stop_reason": r.get("stop_reason"), "cost": r.get("total_cost_usd"),
                                         "turns": r.get("num_turns")}
        time.sleep(60 * (attempt + 1))  # usage limits and overloads clear on their own
    raise APIError("claude -p failed: %s" % str(r.get("result"))[:300])


def cli_messages(model, system, user):
    """A single turn for the judge: system prompt replaced, no tools, no settings, empty directory."""
    with tempfile.TemporaryDirectory() as d:
        open(os.path.join(d, "system.txt"), "w").write(system)
        return cli_run(["--model", model, "--system-prompt-file", "system.txt", "--tools", "",
                        "--setting-sources", ""], user, d, 900)


def workspace_files(ws, given=None):
    """What an agent run left behind, as text the judge can read. Files the run wrote or changed
    come first; the eval's untouched input files follow, marked, with whatever room is left.
    Office files go through file-to-markdown; other binaries are listed by name and size."""
    parts, budget, found = [], 90000, []
    for base, dirs, files in os.walk(ws):
        dirs[:] = sorted(d for d in dirs if not (base == ws and d in (".claude", "skills"))
                         and d not in (".git", "node_modules", "__pycache__", ".venv", "venv"))
        for name in sorted(files):
            path = os.path.join(base, name)
            rel = os.path.relpath(path, ws)
            src = os.path.join(given, rel) if given else None
            same = bool(src and os.path.isfile(src) and open(src, "rb").read() == open(path, "rb").read())
            found.append((same, rel, path))
    for n, (same, rel, path) in enumerate(sorted(found)):
        if budget <= 0 or n >= 60:
            parts.append("[%d more file(s) not shown]" % (len(found) - n))
            break
        name, tag = os.path.basename(path), ' input="true"' if same else ""
        body = None
        if name.lower().endswith((".docx", ".xlsx", ".pptx")):
            v = subprocess.run([sys.executable, VIEWER, path, "-o", "-"], capture_output=True, text=True)
            body = v.stdout if v.returncode == 0 else None
        else:
            try:
                body = open(path, encoding="utf-8").read()
            except (UnicodeDecodeError, OSError):
                pass
        if body is None:
            parts.append('<file path="%s"%s bytes="%d" binary="true"/>' % (rel, tag, os.path.getsize(path)))
            continue
        shown = body[:min(12000, max(budget, 0))]
        budget -= len(shown)
        if len(shown) < len(body):  # say so: a silently cut file reads to the judge as an empty one
            shown += "\n[%d of %d characters shown; the file continues]" % (len(shown), len(body))
        parts.append('<file path="%s"%s chars="%d">\n%s\n</file>' % (rel, tag, len(body), shown))
    return "\n".join(parts)


def fixtures(skill, eval_id):
    """evals/files/<eval id>/ holds the input files an eval's prompt names. They are copied into
    the working directory for both arms."""
    d = os.path.join(catalog.skill_dir(skill), "evals", "files", str(eval_id))
    return d if os.path.isdir(d) else None


def digest(d):
    h = hashlib.sha256()
    for base, dirs, files in os.walk(d):
        dirs.sort()
        for name in sorted(files):
            path = os.path.join(base, name)
            h.update(os.path.relpath(path, d).encode() + b"\0" + open(path, "rb").read())
    return h.hexdigest()[:16]


def cli_agent(model, system, user, skill=None, files=None):
    """A real agent run: Claude Code with its own system prompt and file and shell tools, in a
    throwaway directory, sandboxed, with no settings, plugins or MCP servers from this machine.
    `system` is appended to Claude Code's prompt. The skill arm also gets the skill's folder at
    skills/<name>/, the path a plain-copy install uses. Returns the final message followed by
    the files the run left behind."""
    with tempfile.TemporaryDirectory() as ws, tempfile.TemporaryDirectory() as side:
        ws = os.path.realpath(ws)
        env = dict(os.environ)
        if files:
            shutil.copytree(files, ws, dirs_exist_ok=True)
        if skill:
            dest = os.path.join(ws, "skills", skill)
            shutil.copytree(catalog.skill_dir(skill), dest, ignore=shutil.ignore_patterns("evals", "__pycache__"))
            env["CLAUDE_SKILL_DIR"] = dest
        sysfile = os.path.join(side, "system.txt")
        open(sysfile, "w").write(system)
        text, resp = cli_run(["--model", model, "--append-system-prompt-file", sysfile, "--restricted",
                              "--tools", "Read,Write,Edit,Glob,Grep,Bash", "--permission-mode", "acceptEdits",
                              "--settings", CLI_SANDBOX, "--max-budget-usd", "3"], user, ws, 1200, env)
        left = workspace_files(ws, files)
        return text + ("\n\n<files_in_workspace>\n%s\n</files_in_workspace>" % left if left else ""), resp


class BudgetExceeded(Exception):
    pass


class Budget(object):
    """Spend tracker. Checked before each paid call, so a run overshoots by at most the calls
    already in flight."""

    def __init__(self, limit):
        self.limit, self.spent, self.lock = limit, 0.0, threading.Lock()

    def check(self):
        with self.lock:
            if self.spent >= self.limit:
                raise BudgetExceeded()

    def add(self, cost):
        with self.lock:
            self.spent += cost


def price(model):
    for name, p in PRICES.items():  # a dated snapshot id (claude-haiku-4-5-20251001) prices as its alias
        if model == name or model.startswith(name + "-2"):
            return p
    return None


def cost_of(model, usage):
    pin, pout = price(model)
    tokens_in = (usage.get("input_tokens", 0) + 0.1 * usage.get("cache_read_input_tokens", 0)
                 + 1.25 * usage.get("cache_creation_input_tokens", 0))
    return (tokens_in * pin + usage.get("output_tokens", 0) * pout) / 1e6


def cache_path(kind, model, system, user, trial, files=None):
    parts = [kind, model, system, user, trial] + ([BACKEND + "/agent-1"] if BACKEND != "api" else [])
    if files and BACKEND != "api":
        parts.append(digest(files))
    key = hashlib.sha256(json.dumps(parts).encode()).hexdigest()
    return os.path.join(CACHE, key[:2], key + ".json")


def call(kind, model, system, user, trial, max_tokens, budget, skill=None, files=None):
    """One model call, cached on everything that determines it. Returns a record with the text,
    the API's usage block, the cost at this model's rate, and whether it came from the cache."""
    path = cache_path(kind, model, system, user, trial, files)
    if os.path.exists(path):
        return dict(json.load(open(path)), cached=True)
    budget.check()
    start = time.time()
    if BACKEND == "claude-cli":
        text, resp = cli_agent(model, system, user, skill, files) if kind == "gen" else cli_messages(model, system, user)
    else:
        text, resp = messages(model, system, user, max_tokens=max_tokens, timeout=600, raw=True)
    served = resp.get("model", "")
    if not (served == model or served.startswith(model) or model.startswith(served)):
        raise APIError(f"asked for {model}, served by {served}")
    usage = resp.get("usage", {})
    rec = {"text": text, "usage": usage, "model": served, "stop_reason": resp.get("stop_reason"),
           "seconds": round(time.time() - start, 1), "turns": resp.get("turns"),
           "cost": resp["cost"] if resp.get("cost") is not None else cost_of(model, usage)}
    budget.add(rec["cost"])
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = "%s.%d.tmp" % (path, threading.get_ident())
    with open(tmp, "w") as f:
        json.dump(rec, f)
    os.replace(tmp, path)  # atomic: another worker never reads a half-written record
    return dict(rec, cached=False)


def judge(judge_model, output, asserts, trial, budget):
    """Assertion grading through the same cache and budget as generation."""
    def send(model, system, user, max_tokens):
        rec = call("judge", model, system, user, trial, max_tokens, budget)
        return rec["text"], rec
    return grade(judge_model, output, asserts, send)


def pair(judge_model, prompt, a, b, seed, trial, budget):
    """Blind pairwise preference. Which output is shown as A is fixed by the eval, not by the arm."""
    flip = int(hashlib.sha256(seed.encode()).hexdigest(), 16) % 2 == 1
    first, second = (b, a) if flip else (a, b)
    rec = call("pair", judge_model, PAIR_SYSTEM,
               f"<request>\n{prompt}\n</request>\n\n<response_A>\n{first}\n</response_A>\n\n"
               f"<response_B>\n{second}\n</response_B>", trial, 300, budget)
    try:
        v = json.loads(rec["text"][rec["text"].index("{"):rec["text"].rindex("}") + 1])
    except ValueError:
        v = {}
    w = str(v.get("winner", "")).upper()
    winner = "tie" if w not in ("A", "B") else ("baseline" if (w == "A") == flip else "skill")
    return {"winner": winner, "why": v.get("why", "not judged"), "cost": rec["cost"]}


NONINTERACTIVE = ("This is a non-interactive run: the user cannot answer follow-up questions. Work "
                  "with what the request gives you.")


def arm_systems(skill, md):
    """(arm, system text) pairs. Through the API the text is the whole system prompt; through
    Claude Code it is appended to Claude Code's own prompt, so the baseline is plain Claude Code."""
    if BACKEND == "claude-cli":
        return (("skill", skill_system(md) + f"\n\nThis skill's folder is at skills/{skill}/ in the working "
                 "directory (CLAUDE_SKILL_DIR points to it)."), ("baseline", NONINTERACTIVE))
    return (("skill", skill_system(md)), ("baseline", BASELINE_SYSTEM))


def run_unit(unit, judge_model, budget):
    s, e, model, trial = unit
    row = {"skill": s, "eval": e.get("id"), "model": model, "trial": trial, "arms": {}}
    md = open(os.path.join(catalog.skill_dir(s), "SKILL.md")).read()
    try:
        for arm, system in arm_systems(s, md):
            gen = call("gen", model, system, e["prompt"], trial, 16000, budget, s if arm == "skill" else None,
                       fixtures(s, e.get("id")))
            grades, jrec = judge(judge_model, gen["text"], e["assertions"], trial, budget)
            row["arms"][arm] = {"output": gen["text"], "usage": gen["usage"], "cost": gen["cost"],
                                "seconds": gen["seconds"], "stop_reason": gen["stop_reason"],
                                "turns": gen.get("turns"),
                                "grades": grades, "judge_cost": jrec["cost"]}
        row["pairwise"] = pair(judge_model, e["prompt"], row["arms"]["skill"]["output"],
                               row["arms"]["baseline"]["output"], f"{s}/{e.get('id')}/{model}/{trial}",
                               trial, budget)
    except BudgetExceeded:
        row["skipped"] = "budget"
    except (APIError, json.JSONDecodeError) as err:
        row["error"] = str(err)
    return row


def run_floor(unit, judge_model, budget):
    s, e = unit
    try:
        grades, jrec = judge(judge_model, FLOOR_OUTPUT, e["assertions"], 0, budget)
        return {"skill": s, "eval": e.get("id"), "grades": grades, "judge_cost": jrec["cost"]}
    except BudgetExceeded:
        return {"skill": s, "eval": e.get("id"), "skipped": "budget"}
    except (APIError, json.JSONDecodeError) as err:
        return {"skill": s, "eval": e.get("id"), "error": str(err)}


# --------------------------------------------------------------------------- statistics

def mean(xs):
    return sum(xs) / len(xs) if xs else 0.0


def met(grades):
    return mean([1.0 if g["pass"] else 0.0 for g in grades])


def boot(xs, n=2000):
    """95% bootstrap interval for the mean, resampling evals. Fixed seed: same data, same interval."""
    if len(xs) < 2:
        return None
    rng = random.Random(0)
    means = sorted(mean(rng.choices(xs, k=len(xs))) for _ in range(n))
    return means[int(0.025 * n)], means[int(0.975 * n)]


def by_eval(rows, model, value):
    """{(skill, eval): mean of value(row) over trials} for one model's completed rows."""
    acc = {}
    for r in rows:
        if r["model"] == model and "pairwise" in r:
            acc.setdefault((r["skill"], r["eval"]), []).append(value(r))
    return {k: mean(v) for k, v in acc.items()}


def summarize(rows, floor, models, labels, tolerance):
    out = {"models": {}, "routing": []}
    floor_ok = [f for f in floor if "grades" in f]
    out["floor"] = mean([met(f["grades"]) for f in floor_ok]) if floor_ok else None
    for m in models:
        sk = by_eval(rows, m, lambda r: met(r["arms"]["skill"]["grades"]))
        ba = by_eval(rows, m, lambda r: met(r["arms"]["baseline"]["grades"]))
        win = by_eval(rows, m, lambda r: {"skill": 1.0, "tie": 0.5, "baseline": 0.0}[r["pairwise"]["winner"]])
        done = [r for r in rows if r["model"] == m and "pairwise" in r]
        lifts = [sk[k] - ba[k] for k in sk]
        spread = {}
        for r in done:
            spread.setdefault((r["skill"], r["eval"]), []).append(met(r["arms"]["skill"]["grades"]))
        out["models"][m] = {
            "label": labels[m], "evals": len(sk), "runs": len(done),
            "skill": mean(list(sk.values())), "baseline": mean(list(ba.values())),
            "lift": mean(lifts), "lift_ci": boot(lifts),
            "win": mean(list(win.values())), "win_ci": boot(list(win.values())),
            "cost_skill": mean([r["arms"]["skill"]["cost"] for r in done]),
            "cost_baseline": mean([r["arms"]["baseline"]["cost"] for r in done]),
            "out_tokens_skill": mean([r["arms"]["skill"]["usage"].get("output_tokens", 0) for r in done]),
            "out_tokens_baseline": mean([r["arms"]["baseline"]["usage"].get("output_tokens", 0) for r in done]),
            "truncated": sum(1 for r in done for a in r["arms"].values() if a["stop_reason"] == "max_tokens"),
            "refused": sum(1 for r in done for a in r["arms"].values() if a["stop_reason"] == "refusal"),
            "trial_range": mean([max(v) - min(v) for v in spread.values() if len(v) > 1]),
            "errors": sum(1 for r in rows if r["model"] == m and "error" in r),
            "skipped": sum(1 for r in rows if r["model"] == m and "skipped" in r),
        }
    out["skills"] = []
    for m in models:
        done = [r for r in rows if r["model"] == m and "pairwise" in r]
        for s in sorted({r["skill"] for r in done}):
            mine = [r for r in done if r["skill"] == s]
            out["skills"].append({
                "skill": s, "model": m, "evals": len({r["eval"] for r in mine}),
                "skill_met": mean([met(r["arms"]["skill"]["grades"]) for r in mine]),
                "baseline_met": mean([met(r["arms"]["baseline"]["grades"]) for r in mine]),
                "preferred": mean([{"skill": 1.0, "tie": 0.5, "baseline": 0.0}[r["pairwise"]["winner"]] for r in mine]),
                "cost_skill": mean([r["arms"]["skill"]["cost"] for r in mine]),
                "cost_baseline": mean([r["arms"]["baseline"]["cost"] for r in mine])})
    if len(models) > 1:
        tiers = json.load(open(os.path.join(ROOT, "model-routing.json")))["skills"]
        cost = {m: sum(price(m)) for m in models}
        per = {m: {} for m in models}
        for m in models:
            for (s, _), v in by_eval(rows, m, lambda r: met(r["arms"]["skill"]["grades"])).items():
                per[m].setdefault(s, []).append(v)
        for s in sorted({s for m in models for s in per[m]}):
            if not all(s in per[m] for m in models):
                continue
            scores = {m: mean(per[m][s]) for m in models}
            best = max(scores.values())
            cheapest = min((m for m in models if scores[m] >= best - tolerance), key=lambda m: cost[m])
            out["routing"].append({"skill": s, "assigned": tiers.get(s, {}).get("tier", "?"),
                                   "scores": scores, "cheapest_adequate": labels[cheapest],
                                   "evals": len(per[models[0]][s])})
    return out


# --------------------------------------------------------------------------- report

def pct(x):
    return "–" if x is None else f"{100 * x:.0f}%"


def ci(pair_, signed=False):
    if not pair_:
        return ""
    fmt = "{:+.0f}" if signed else "{:.0f}"
    return " (" + fmt.format(100 * pair_[0]) + " to " + fmt.format(100 * pair_[1]) + ")"


def report(summary, judge_model, trials, spent, scripted):
    via = ("Claude Code agent runs (`claude -p` with file and shell tools, sandboxed, in an empty "
           "directory); dollars are list price for the tokens used" if BACKEND == "claude-cli"
           else "the Messages API, one turn, no tools")
    lines = ["# Skill benchmark: with the skill and without it", "",
             f"Judge: `{judge_model}` · trials per eval: {trials} · spent this run: ${spent:.2f} · run through {via}", "",
             "| Model | Evals | Assertions met, skill | Baseline | Lift, points (95% CI) | "
             "Preferred blind (95% CI) | $ per run, skill | Baseline |", "|---|---|---|---|---|---|---|---|"]
    for m, d in summary["models"].items():
        lines.append(f"| {d['label']} `{m}` | {d['evals']} | {pct(d['skill'])} | {pct(d['baseline'])} | "
                     f"{100 * d['lift']:+.0f}{ci(d['lift_ci'], True)} | {pct(d['win'])}{ci(d['win_ci'])} | "
                     f"${d['cost_skill']:.4f} | ${d['cost_baseline']:.4f} |")
    lines += ["", f"**Floor: a non-answer meets {pct(summary['floor'])} of assertions.** Assertions phrased as "
              "\"does not…\" pass when nothing is written, so read both columns against this number.", "",
              "- *Assertions met* is the mean over evals of the share of that eval's assertions the judge "
              "marked met. The skill's author wrote those assertions, so the baseline is graded on a rubric "
              "it never saw.",
              "- *Preferred blind* is the share of pairs where a judge that saw neither the assertions nor "
              "the skill picked the skill's output (a tie counts half). 50% means no preference.",
              "- Intervals resample evals, not trials. An interval that spans 0 (lift) or 50% (preference) "
              "is not a result."]
    notes = []
    for m, d in summary["models"].items():
        bits = []
        if d["truncated"]:
            bits.append(f"{d['truncated']} output(s) hit the token limit")
        if d["refused"]:
            bits.append(f"{d['refused']} refusal(s)")
        if d["errors"]:
            bits.append(f"{d['errors']} API error(s)")
        if d["skipped"]:
            bits.append(f"{d['skipped']} run(s) skipped when the budget ran out")
        if trials > 1:
            bits.append(f"skill pass rate moved {100 * d['trial_range']:.0f} points between trials of the "
                        "same eval, on average")
        bits.append(f"output tokens per run: {d['out_tokens_skill']:.0f} with the skill, "
                    f"{d['out_tokens_baseline']:.0f} without")
        notes.append(f"- `{m}`: " + "; ".join(bits))
    lines += ["", "## Run notes", ""] + notes
    if summary["routing"]:
        models = list(summary["models"])
        lines += ["", "## Routing check", "",
                  "Per skill: assertions met with the skill on each model, and the cheapest model within the "
                  "tolerance of the best. One or two evals per skill makes each row a prompt to look, not a "
                  "verdict.", "",
                  "| Skill | Evals | Assigned tier | " + " | ".join(summary["models"][m]["label"] for m in models)
                  + " | Cheapest adequate |", "|---|---|---|" + "---|" * (len(models) + 1)]
        for r in summary["routing"]:
            flag = "" if r["cheapest_adequate"] == r["assigned"] else " ⟵ differs"
            lines.append(f"| `{r['skill']}`{'†' if r['skill'] in scripted else ''} | {r['evals']} | {r['assigned']} | "
                         + " | ".join(pct(r["scores"][m]) for m in models) + f" | {r['cheapest_adequate']}{flag} |")
        lines += ["", ""]
        lines[-1] = "† ships a script."
        if BACKEND == "api":
            lines[-1] += " This run has no tools, so the model describes the run instead of doing it."
    lines += ["", ("Each run is a full agent session, graded on its final message and the files it wrote. "
                   if BACKEND == "claude-cli" else "One user turn and no tools. ")
              + "The judge is a model. Outputs, grades and token counts for every run are in results.json."]
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------- main

def resolve_models(spec):
    routing = json.load(open(os.path.join(ROOT, "model-routing.json")))
    tiers = routing["providers"][routing["active_provider"]]["models"]
    models, labels = [], {}
    for name in [x.strip() for x in spec.split(",") if x.strip()]:
        m = tiers.get(name, name)
        if price(m) is None:
            sys.exit(f"no price for model {m!r}: add it to PRICES in run_bench.py, so the budget can be enforced")
        models.append(m)
        labels[m] = name if name in tiers else m
    return models, labels


def estimate(units, floor_units, judge_model):
    """Rough dollars for the calls not yet cached: characters / 4 as tokens, and an assumed
    4,000 output tokens per generation. Printed as an estimate; the run itself bills from usage."""
    total, fresh = 0.0, 0
    jin, jout = price(judge_model)
    for s, e, model, trial in units:
        md = open(os.path.join(catalog.skill_dir(s), "SKILL.md")).read()
        pin, pout = price(model)
        for _, system in arm_systems(s, md):
            fresh += not os.path.exists(cache_path("gen", model, system, e["prompt"], trial, fixtures(s, e.get("id"))))
            total += ((len(system) + len(e["prompt"])) / 4 * pin + 4000 * pout) / 1e6
            total += (4500 * jin + 500 * jout) / 1e6          # assertion judge reads one output
        total += (9000 * jin + 100 * jout) / 1e6              # pairwise judge reads both
    total += len(floor_units) * (400 * jin + 500 * jout) / 1e6
    return total, fresh


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--skills", help="comma-separated skill names (default: all)")
    ap.add_argument("--models", default="standard",
                    help="comma-separated tiers from model-routing.json (light, standard, heavy) or model ids")
    ap.add_argument("--backend", choices=("api", "claude-cli"), default="api",
                    help="api needs ANTHROPIC_API_KEY; claude-cli runs each call through a signed-in `claude -p`")
    ap.add_argument("--judge-model", default=JUDGE_MODEL)
    ap.add_argument("--trials", type=int, default=1, help="runs per eval per arm (default 1)")
    ap.add_argument("--budget", type=float, default=5.0, help="hard stop in USD for this run (default 5)")
    ap.add_argument("--tolerance", type=float, default=0.05,
                    help="routing check: a model within this of the best score counts as adequate (default 0.05)")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--no-floor", action="store_true", help="skip grading the non-answer")
    ap.add_argument("--dry-run", action="store_true", help="count calls and estimate cost; spend nothing")
    ap.add_argument("--out", default="bench-results", help="directory for results.json and report.md")
    ap.add_argument("--publish", metavar="FILE",
                    help="also write the summary (no outputs) to FILE; docs/benchmarks/latest.json is what the site reads")
    a = ap.parse_args()

    global BACKEND
    BACKEND = a.backend
    all_skills = catalog.skills()
    skills = [s.strip() for s in a.skills.split(",")] if a.skills else all_skills
    unknown = [s for s in skills if s not in all_skills]
    if unknown:
        sys.exit(f"unknown skill(s): {', '.join(unknown)}")
    models, labels = resolve_models(a.models)
    if price(a.judge_model) is None:
        sys.exit(f"no price for judge model {a.judge_model!r}: add it to PRICES in run_bench.py")
    evals = [(s, e) for s in skills for e in (load(s, "evals.json") or {}).get("evals", [])]
    units = [(s, e, m, t) for s, e in evals for m in models for t in range(a.trials)]
    floor_units = [] if a.no_floor else evals

    est, fresh = estimate(units, floor_units, a.judge_model)
    print(f"{len(evals)} eval(s) across {len(skills)} skill(s) x {len(models)} model(s) x {a.trials} trial(s): "
          f"{2 * len(units)} generations ({fresh} not cached), {2 * len(units) + len(floor_units)} assertion "
          f"gradings, {len(units)} pairwise judgements. Rough cost if nothing is cached: ${est:.2f}. "
          f"Budget: ${a.budget:.2f}.")
    if a.dry_run:
        return 0
    if BACKEND == "api" and not api_key():
        print("::notice::ANTHROPIC_API_KEY is not set — nothing was run. Export it and rerun; "
              "--dry-run shows the size of a run without it, and --backend claude-cli runs "
              "through a signed-in Claude Code instead.")
        return 0

    budget = Budget(a.budget)
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        rows = list(ex.map(lambda u: run_unit(u, a.judge_model, budget), units))
        floor = list(ex.map(lambda u: run_floor(u, a.judge_model, budget), floor_units))
    summary = summarize(rows, floor, models, labels, a.tolerance)
    scripted = {s for s in skills if os.path.isdir(os.path.join(catalog.skill_dir(s), "scripts"))}
    md = report(summary, a.judge_model, a.trials, budget.spent, scripted)
    os.makedirs(a.out, exist_ok=True)
    json.dump({"backend": BACKEND, "judge_model": a.judge_model, "models": models, "trials": a.trials, "spent": budget.spent,
               "summary": summary, "floor": floor, "runs": rows},
              open(os.path.join(a.out, "results.json"), "w"), indent=2)
    open(os.path.join(a.out, "report.md"), "w").write(md)
    if a.publish:
        os.makedirs(os.path.dirname(os.path.abspath(a.publish)), exist_ok=True)
        with open(a.publish, "w") as f:
            json.dump({"date": time.strftime("%Y-%m-%d"), "backend": BACKEND, "judge_model": a.judge_model,
                       "trials": a.trials, "scripted": sorted(scripted), **summary}, f, indent=1)
            f.write("\n")
    print(md)
    step = os.environ.get("GITHUB_STEP_SUMMARY")
    if step:
        with open(step, "a") as f:
            f.write(md)
    if budget.spent >= a.budget:
        print(f"stopped at the ${a.budget:.2f} budget; rerun with a higher --budget to finish (cached calls are free)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

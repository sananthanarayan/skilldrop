#!/usr/bin/env python3
"""Measure what a skill is worth: the same request with the skill and without it.

run_evals.py asks "does the skill's output meet its assertions?". This asks the question that
number can't answer alone: "compared to what, and at what cost?". For every eval in a skill's
evals/evals.json it runs a paired comparison on each model:

  skill     SKILL.md is the system prompt (what run_evals.py does)
  baseline  the same request with no skill, only a one-line agent prompt
  floor     a non-answer, graded like any output. Shows how many assertions pass vacuously
            ("does not invent rows"), so the other two numbers have a zero to stand on.
  tools     with --tools-arm (claude-cli only), for a skill that ships scripts: its scripts and
            the data they read, with no instructions, only a generated list of the scripts. It is
            judged against the plain agent and against the skill, so a losing skill says whether
            its instructions or its scripts carry the result (RFC-0067).

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
into the working directory for both arms (claude-cli only). A git-history.json there turns
the directory into a git repository with that history (see build_git_history), for a skill
that reads commits.

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
import privacy
from anthropic_api import APIError, api_key, messages
from run_evals import grade, load, skill_system

ROOT = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(ROOT, ".bench-cache")
JUDGE_MODEL = "claude-sonnet-5-5"

# USD per million tokens (input, output), Anthropic first-party rates as of 2026-10-06.
# A cache read bills at 0.1x input and a cache write at 1.25x input.
PRICES = {
    "claude-haiku-4-5": (1.0, 5.0),
    "claude-haiku-5-5": (0.1, 0.5),  # prompts up to 100K tokens; 0.5 / 2.5 beyond
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
SECOND_JUDGE = None  # a second pairwise judge, set from --second-judge
TOOLS_ARM = False  # also run each scripted skill's tools without its instructions, set from --tools-arm

# What the tools arm leaves out of a skill's folder: its instructions. Data the scripts read,
# such as templates/, stays, so every script still runs.
INSTRUCTIONS = ("SKILL.md", "reference.md", "manifest.json", "examples", "evals", "__pycache__")


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
        except subprocess.TimeoutExpired:
            # a session that hangs once will hang again; retrying it three times stalls the whole run
            raise APIError("claude -p timed out after %d seconds" % timeout)
        except (ValueError, OSError) as err:
            r = {"is_error": True, "result": str(err)[:300]}
        if not r.get("is_error"):
            used = r.get("modelUsage", {})
            # Claude Code makes small side calls on a lighter model. A short reply (a judge's
            # verdict) can produce fewer output tokens than those, so the model that answered is
            # the one asked for when it produced any output, and the busiest model otherwise.
            asked = cmd[cmd.index("--model") + 1] if "--model" in cmd else ""
            served = [m for m in used if m.startswith(asked) and used[m].get("outputTokens", 0)] if asked else []
            served = served or sorted(used, key=lambda m: -used[m].get("outputTokens", 0))
            return r.get("result", ""), {"model": served[0] if served else "", "usage": r.get("usage", {}),
                                         "stop_reason": r.get("stop_reason"), "cost": cli_cost(r),
                                         "turns": r.get("num_turns")}
        time.sleep(60 * (attempt + 1))  # usage limits and overloads clear on their own
    raise APIError("claude -p failed: %s" % str(r.get("result"))[:300])


def cli_cost(r):
    """The cost Claude Code reports, except for a model it has no price for (costBasis "unknown"),
    which it bills at a placeholder rate: that model's tokens are priced from PRICES instead."""
    used = r.get("modelUsage") or {}
    if not any(u.get("costBasis") == "unknown" for u in used.values()):
        return r.get("total_cost_usd")
    total = 0.0
    for m, u in used.items():
        if u.get("costBasis") == "unknown" and price(m):
            total += cost_of(m, {"input_tokens": u.get("inputTokens", 0), "output_tokens": u.get("outputTokens", 0),
                                 "cache_read_input_tokens": u.get("cacheReadInputTokens", 0),
                                 "cache_creation_input_tokens": u.get("cacheCreationInputTokens", 0)})
        else:
            total += u.get("costUSD", 0.0)
    return total


def cli_messages(model, system, user):
    """A single turn for the judge: system prompt replaced, no tools, no settings, empty directory."""
    with tempfile.TemporaryDirectory() as d:
        open(os.path.join(d, "system.txt"), "w", encoding="utf-8").write(system)
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
    if os.path.isdir(os.path.join(ws, ".git")):
        # An eval with git-history.json runs in a real repository. The judge sees the history the
        # agent could read, or it would take every commit the reply cites for an invention.
        log = subprocess.run(["git", "log", "--date=short", "--stat", "-p", "--format=commit %h%nAuthor: %an%nDate: %ad%n%n    %s%n%b"],
                             cwd=ws, capture_output=True, text=True, encoding="utf-8", errors="replace")
        text = log.stdout if log.returncode == 0 else ""
        if text:
            shown = text[:30000]
            if len(shown) < len(text):
                shown += "\n[%d of %d characters shown; the history continues]" % (len(shown), len(text))
            parts.append('<git-history input="true" note="the git log of the working directory, which the agent could read">\n%s\n</git-history>' % shown)
    return "\n".join(parts)


def fixtures(skill, eval_id):
    """evals/files/<eval id>/ holds the input files an eval's prompt names. They are copied into
    the working directory for both arms."""
    d = os.path.join(catalog.skill_dir(skill), "evals", "files", str(eval_id))
    return d if os.path.isdir(d) else None


FIXTURE = ".fixture"


def workspace_name(rel):
    """A dependency file in a fixture (package.json, go.mod, a CI workflow) is kept in the repo
    as <name>.fixture, so GitHub's dependency graph never reads a fake project's pins as ours
    and raises alerts against code nothing runs (validate.py enforces it). The run sees the
    real name."""
    return rel[:-len(FIXTURE)] if rel.endswith(FIXTURE) else rel


GIT_HISTORY = "git-history.json"


def copy_fixtures(src, dest):
    for base, _, files in os.walk(src):
        for name in files:
            rel = os.path.relpath(os.path.join(base, name), src)
            if rel == GIT_HISTORY:
                continue
            out = os.path.join(dest, workspace_name(rel))
            os.makedirs(os.path.dirname(out), exist_ok=True)
            shutil.copy2(os.path.join(base, name), out)
    if os.path.isfile(os.path.join(src, GIT_HISTORY)):
        with open(os.path.join(src, GIT_HISTORY), encoding="utf-8") as fh:
            build_git_history(dest, json.load(fh))


def build_git_history(ws, history):
    """A real git history for a fixture, from git-history.json, so it lives in the repo as
    reviewable text rather than as a nested .git folder git can't commit:

      {"start": {"date": "2025-01-10", "author": "Ana", "message": "Initial import"},
       "commits": [{"date": "2025-03-02", "author": "Ben", "message": "Switch to SQS",
                    "files": {"services/orders/publish.py": "...", "old.txt": null}}]}

    The fixture's other files are the first commit ("start"); each later commit writes its
    files, or deletes the ones set to null. The working tree ends at the last commit. Dates are
    the author and committer dates, at noon UTC, so `git log --since` reads them as written."""
    def git(*args, author="Fixture", date="2025-01-01"):
        stamp = "%sT12:00:00+00:00" % date
        env = dict(os.environ, GIT_AUTHOR_NAME=author, GIT_AUTHOR_EMAIL="%s@example.invalid" % author.lower().replace(" ", "."),
                   GIT_COMMITTER_NAME=author, GIT_COMMITTER_EMAIL="%s@example.invalid" % author.lower().replace(" ", "."),
                   GIT_AUTHOR_DATE=stamp, GIT_COMMITTER_DATE=stamp, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull)
        subprocess.run(["git", "-c", "init.defaultBranch=main", "-c", "commit.gpgsign=false", "-c", "core.hooksPath=" + os.devnull,
                        *args], cwd=ws, env=env, check=True, capture_output=True)
    start = history.get("start") or {}
    git("init", "-q")
    git("add", "-A")
    git("commit", "-q", "--allow-empty", "-m", start.get("message", "Initial import"),
        author=start.get("author", "Fixture"), date=start.get("date", "2025-01-01"))
    for c in history.get("commits", []):
        for rel, text in (c.get("files") or {}).items():
            path = os.path.join(ws, *rel.split("/"))
            if not os.path.realpath(path).startswith(os.path.realpath(ws) + os.sep):
                raise ValueError("git-history.json writes outside the fixture: %s" % rel)
            if text is None:
                if os.path.exists(path):
                    os.remove(path)
            else:
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(text)
        git("add", "-A")
        git("commit", "-q", "--allow-empty", "-m", c["message"], author=c.get("author", "Fixture"), date=c["date"])


def digest(d):
    """Hashes the names a run sees, so renaming a file to <name>.fixture keeps its cache."""
    h = hashlib.sha256()
    for base, dirs, files in os.walk(d):
        dirs.sort()
        for name in sorted(files, key=lambda n: workspace_name(n)):
            path = os.path.join(base, name)
            h.update(workspace_name(os.path.relpath(path, d)).encode() + b"\0" + open(path, "rb").read())
    return h.hexdigest()[:16]


def has_scripts(skill):
    d = os.path.join(catalog.skill_dir(skill), "scripts")
    return os.path.isdir(d) and any(n.endswith((".py", ".js", ".sh")) for n in os.listdir(d))


def tools_system(skill):
    """The tools arm's whole instruction: where the scripts are, and each one's own first
    docstring or comment line. Generated, never written by hand, so it carries none of the
    skill's rules."""
    import ast
    d = os.path.join(catalog.skill_dir(skill), "scripts")
    lines = []
    for name in sorted(os.listdir(d)):
        path = os.path.join(d, name)
        if not name.endswith((".py", ".js", ".sh")) or not os.path.isfile(path):
            continue
        first = ""
        try:
            with open(path, encoding="utf-8") as fh:
                src = fh.read()
            if name.endswith(".py"):
                first = (ast.get_docstring(ast.parse(src)) or "").strip().split("\n")[0]
            else:
                m = next((l for l in src.splitlines()[1:12] if l.strip().startswith(("//", "#", "*"))), "")
                first = m.strip().lstrip("/#* ").strip()
        except (SyntaxError, UnicodeDecodeError, ValueError):
            pass
        lines.append("- skills/%s/scripts/%s%s" % (skill, name, (": " + first) if first else ""))
    return (NONINTERACTIVE + "\n\nScripts that may help with this kind of task are in the working "
            "directory. Run one with --help to see what it takes.\n" + "\n".join(lines))


def scripts_digest(skill):
    """The tools arm is measuring the scripts, so a changed script must not reuse a cached run."""
    h = hashlib.sha256()
    root = catalog.skill_dir(skill)
    for base, dirs, names in os.walk(root):
        dirs[:] = sorted(x for x in dirs if x not in INSTRUCTIONS)
        if os.path.relpath(base, root) == ".":
            names = [n for n in names if n not in INSTRUCTIONS]
        for n in sorted(names):
            path = os.path.join(base, n)
            with open(path, "rb") as fh:
                # "/" on every OS, so the same scripts give the same key on Windows too
                h.update(os.path.relpath(path, root).replace(os.sep, "/").encode() + b"\0" + fh.read())
    return h.hexdigest()[:16]


def stage_skill(skill, ws, layout="full"):
    """Copy a skill into the working directory at skills/<name>/, as a plain-copy install does.
    The tools layout leaves out its instructions and keeps the scripts and the data they read."""
    dest = os.path.join(ws, "skills", skill)
    ignore = INSTRUCTIONS if layout == "tools" else ("evals", "__pycache__")
    shutil.copytree(catalog.skill_dir(skill), dest, ignore=shutil.ignore_patterns(*ignore))
    return dest


def cli_agent(model, system, user, skill=None, files=None, layout="full"):
    """A real agent run: Claude Code with its own system prompt and file and shell tools, in a
    throwaway directory, sandboxed, with no settings, plugins or MCP servers from this machine.
    `system` is appended to Claude Code's prompt. The skill arm also gets the skill's folder at
    skills/<name>/, the path a plain-copy install uses. Returns the final message followed by
    the files the run left behind."""
    with tempfile.TemporaryDirectory() as ws, tempfile.TemporaryDirectory() as side:
        ws = os.path.realpath(ws)
        env = dict(os.environ)
        if files:
            copy_fixtures(files, ws)
        if skill:
            dest = stage_skill(skill, ws, layout)
            if layout != "tools":
                env["CLAUDE_SKILL_DIR"] = dest
        sysfile = os.path.join(side, "system.txt")
        open(sysfile, "w", encoding="utf-8").write(system)
        text, resp = cli_run(["--model", model, "--append-system-prompt-file", sysfile, "--restricted",
                              "--tools", "Read,Write,Edit,Glob,Grep,Bash", "--permission-mode", "acceptEdits",
                              "--settings", CLI_SANDBOX, "--max-budget-usd", "3"], user, ws, 900, env)
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


def cache_path(kind, model, system, user, trial, files=None, extra=None):
    parts = [kind, model, system, user, trial] + ([BACKEND + "/agent-1"] if BACKEND != "api" else [])
    if extra:
        parts.append(extra)
    if files and BACKEND != "api":
        parts.append(digest(files))
        if os.path.isfile(os.path.join(files, GIT_HISTORY)):
            parts.append("git-history-shown-to-judge")  # runs from before the judge saw it are stale
    key = hashlib.sha256(json.dumps(parts).encode()).hexdigest()
    return os.path.join(CACHE, key[:2], key + ".json")


def call(kind, model, system, user, trial, max_tokens, budget, skill=None, files=None, layout="full"):
    """One model call, cached on everything that determines it. Returns a record with the text,
    the API's usage block, the cost at this model's rate, and whether it came from the cache."""
    extra = ("tools/" + scripts_digest(skill)) if layout == "tools" else None
    path = cache_path(kind, model, system, user, trial, files, extra)
    if os.path.exists(path):
        return dict(json.load(open(path, encoding="utf-8")), cached=True)
    budget.check()
    start = time.time()
    if BACKEND == "claude-cli":
        text, resp = cli_agent(model, system, user, skill, files, layout) if kind == "gen" else cli_messages(model, system, user)
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
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(rec, f)
    os.replace(tmp, path)  # atomic: another worker never reads a half-written record
    return dict(rec, cached=False)


def judge(judge_model, output, asserts, trial, budget):
    """Assertion grading through the same cache and budget as generation."""
    def send(model, system, user, max_tokens):
        rec = call("judge", model, system, user, trial, max_tokens, budget)
        return rec["text"], rec
    return grade(judge_model, output, asserts, send)


def pair(judge_model, prompt, a, b, seed, trial, budget, names=("skill", "baseline")):
    """Blind pairwise preference. Which output is shown as A is fixed by the eval, not by the arm.
    `names` labels a and b in the result."""
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
    winner = "tie" if w not in ("A", "B") else (names[1] if (w == "A") == flip else names[0])
    return {"winner": winner, "why": v.get("why", "not judged"), "cost": rec["cost"]}


NONINTERACTIVE = ("This is a non-interactive run: the user cannot answer follow-up questions. Work "
                  "with what the request gives you.")


def arm_systems(skill, md):
    """(arm, system text) pairs. Through the API the text is the whole system prompt; through
    Claude Code it is appended to Claude Code's own prompt, so the baseline is plain Claude Code."""
    if BACKEND == "claude-cli":
        arms = (("skill", skill_system(md) + f"\n\nThis skill's folder is at skills/{skill}/ in the working "
                 "directory (CLAUDE_SKILL_DIR points to it)."), ("baseline", NONINTERACTIVE))
        if TOOLS_ARM and has_scripts(skill):
            arms += (("tools", tools_system(skill)),)
        return arms
    return (("skill", skill_system(md)), ("baseline", BASELINE_SYSTEM))


def run_unit(unit, judge_model, budget):
    s, e, model, trial = unit
    row = {"skill": s, "eval": e.get("id"), "model": model, "trial": trial, "arms": {}}
    md = open(os.path.join(catalog.skill_dir(s), "SKILL.md"), encoding="utf-8").read()
    try:
        for arm, system in arm_systems(s, md):
            gen = call("gen", model, system, e["prompt"], trial, 16000, budget, s if arm != "baseline" else None,
                       fixtures(s, e.get("id")), "tools" if arm == "tools" else "full")
            grades, jrec = judge(judge_model, gen["text"], e["assertions"], trial, budget)
            row["arms"][arm] = {"output": gen["text"], "usage": gen["usage"], "cost": gen["cost"],
                                "seconds": gen["seconds"], "stop_reason": gen["stop_reason"],
                                "turns": gen.get("turns"),
                                "grades": grades, "judge_cost": jrec["cost"]}
        row["pairwise"] = pair(judge_model, e["prompt"], row["arms"]["skill"]["output"],
                               row["arms"]["baseline"]["output"], f"{s}/{e.get('id')}/{model}/{trial}",
                               trial, budget)
        if SECOND_JUDGE:  # same request, same outputs, same A/B order, a different model
            row["pairwise2"] = pair(SECOND_JUDGE, e["prompt"], row["arms"]["skill"]["output"],
                                    row["arms"]["baseline"]["output"], f"{s}/{e.get('id')}/{model}/{trial}",
                                    trial, budget)
        if "tools" in row["arms"]:
            # The tools against the plain agent: do the scripts help on their own? The skill
            # against the tools: do the instructions add anything on top of the scripts?
            seed = f"{s}/{e.get('id')}/{model}/{trial}"
            for key, a, b, judge_ in (("tools_vs_baseline", "tools", "baseline", judge_model),
                                      ("skill_vs_tools", "skill", "tools", judge_model),
                                      ("tools_vs_baseline2", "tools", "baseline", SECOND_JUDGE),
                                      ("skill_vs_tools2", "skill", "tools", SECOND_JUDGE)):
                if judge_:
                    row[key] = pair(judge_, e["prompt"], row["arms"][a]["output"], row["arms"][b]["output"],
                                    seed + "/" + key.rstrip("2"), trial, budget, names=(a, b))
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


def second_judge(rows, m, done):
    """The second judge's preference, and how often the two judges picked the same side."""
    two = [r for r in done if "pairwise2" in r]
    if not two:
        return {}
    win2 = list(by_eval(two, m, lambda r: {"skill": 1.0, "tie": 0.5, "baseline": 0.0}[r["pairwise2"]["winner"]]).values())
    decided = [r for r in two if "tie" not in (r["pairwise"]["winner"], r["pairwise2"]["winner"])]
    return {"second_judge": SECOND_JUDGE, "win2": mean(win2), "win2_ci": boot(win2),
            "judges_agree": sum(r["pairwise"]["winner"] == r["pairwise2"]["winner"] for r in decided),
            "judges_decided": len(decided)}


def side(winner, name):
    """1 when `name` won the pair, 0.5 for a tie, 0 when the other side won."""
    return 1.0 if winner == name else 0.5 if winner == "tie" else 0.0


def reading(skill_pref, tools_pref, skill_over_tools):
    """What a skill's three-way result suggests, from the pairwise preferences (0 to 1). A lead
    for a person to check against the outputs, never a verdict: a skill has few evals."""
    if skill_over_tools is None or tools_pref is None:
        return None
    if skill_over_tools > 0.5 and skill_pref > 0.5:
        return "instructions help"
    if tools_pref > 0.5 and skill_over_tools <= 0.5:
        return "the scripts carry it"
    if skill_pref < 0.5 and tools_pref < 0.5:
        return "the plain agent is preferred"
    return "mixed"


def tools_summary(rows, m):
    """The tools arm on one model: the three arms on the same evals, and both new pairings."""
    part = [r for r in rows if r["model"] == m and "pairwise" in r and "tools_vs_baseline" in r]
    if not part:
        return {}
    d = {"evals": len(by_eval(part, m, lambda r: 0)), "skills": len({r["skill"] for r in part})}
    for arm in ("skill", "tools", "baseline"):
        d[arm] = mean(list(by_eval(part, m, lambda r, a=arm: met(r["arms"][a]["grades"])).values()))
        d["cost_" + arm] = mean([r["arms"][arm]["cost"] for r in part])
    for key, name in (("pairwise", "skill"), ("tools_vs_baseline", "tools"), ("skill_vs_tools", "skill"),
                      ("pairwise2", "skill"), ("tools_vs_baseline2", "tools"), ("skill_vs_tools2", "skill")):
        have = [r for r in part if key in r]
        if have:
            w = list(by_eval(have, m, lambda r, k=key, n=name: side(r[k]["winner"], n)).values())
            d["win_" + key], d["win_" + key + "_ci"] = mean(w), boot(w)
    return d


def held_out_ids(skills):
    """(skill, eval id) for every eval written without reading the skill, flagged `held_out` in
    its evals.json. The rest were written by the skill's author, and some were revised against."""
    return {(s, e.get("id")) for s in skills for e in (load(s, "evals.json") or {}).get("evals", [])
            if e.get("held_out")}


def by_kind(rows, m, held):
    """The headline measures split by who wrote the eval: its author, or someone who never read
    the skill. Only the second says how a skill does on requests it was not shaped around."""
    out = {}
    for kind, keep in (("author", lambda r: (r["skill"], r["eval"]) not in held),
                       ("held_out", lambda r: (r["skill"], r["eval"]) in held)):
        part = [r for r in rows if r["model"] == m and "pairwise" in r and keep(r)]
        if not part:
            continue
        sk = by_eval(part, m, lambda r: met(r["arms"]["skill"]["grades"]))
        ba = by_eval(part, m, lambda r: met(r["arms"]["baseline"]["grades"]))
        win = list(by_eval(part, m, lambda r: {"skill": 1.0, "tie": 0.5, "baseline": 0.0}[r["pairwise"]["winner"]]).values())
        lifts = [sk[k] - ba[k] for k in sk]
        d = {"evals": len(sk), "skills": len({r["skill"] for r in part}),
             "skill": mean(list(sk.values())), "baseline": mean(list(ba.values())),
             "lift": mean(lifts), "lift_ci": boot(lifts), "win": mean(win), "win_ci": boot(win)}
        two = [r for r in part if "pairwise2" in r]
        if two:
            win2 = list(by_eval(two, m, lambda r: {"skill": 1.0, "tie": 0.5, "baseline": 0.0}[r["pairwise2"]["winner"]]).values())
            d.update({"win2": mean(win2), "win2_ci": boot(win2)})
        out[kind] = d
    return out


def summarize(rows, floor, models, labels, tolerance):
    out = {"models": {}, "routing": []}
    held = held_out_ids(sorted({r["skill"] for r in rows}))
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
            **second_judge(rows, m, done),
            "cost_skill": mean([r["arms"]["skill"]["cost"] for r in done]),
            "cost_baseline": mean([r["arms"]["baseline"]["cost"] for r in done]),
            "out_tokens_skill": mean([r["arms"]["skill"]["usage"].get("output_tokens", 0) for r in done]),
            "out_tokens_baseline": mean([r["arms"]["baseline"]["usage"].get("output_tokens", 0) for r in done]),
            "truncated": sum(1 for r in done for a in r["arms"].values() if a["stop_reason"] == "max_tokens"),
            "refused": sum(1 for r in done for a in r["arms"].values() if a["stop_reason"] == "refusal"),
            "trial_range": mean([max(v) - min(v) for v in spread.values() if len(v) > 1]),
            "errors": sum(1 for r in rows if r["model"] == m and "error" in r),
            "skipped": sum(1 for r in rows if r["model"] == m and "skipped" in r),
            "by_kind": by_kind(rows, m, held),
        }
        tools = tools_summary(rows, m)
        if tools:
            out["models"][m]["tools"] = tools
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
            three = [r for r in mine if "tools_vs_baseline" in r]
            if three:
                row = out["skills"][-1]
                row.update({
                    "tools_met": mean([met(r["arms"]["tools"]["grades"]) for r in three]),
                    "tools_preferred": mean([side(r["tools_vs_baseline"]["winner"], "tools") for r in three]),
                    "skill_over_tools": mean([side(r["skill_vs_tools"]["winner"], "skill") for r in three]),
                    "cost_tools": mean([r["arms"]["tools"]["cost"] for r in three])})
                judges = [("pairwise", "tools_vs_baseline", "skill_vs_tools")]
                if all("pairwise2" in r and "tools_vs_baseline2" in r for r in three):
                    judges.append(("pairwise2", "tools_vs_baseline2", "skill_vs_tools2"))
                    row.update({
                        "preferred2": mean([side(r["pairwise2"]["winner"], "skill") for r in three]),
                        "tools_preferred2": mean([side(r["tools_vs_baseline2"]["winner"], "tools") for r in three]),
                        "skill_over_tools2": mean([side(r["skill_vs_tools2"]["winner"], "skill") for r in three])})
                # The reading needs every judge to agree; otherwise it is mixed.
                reads = {reading(mean([side(r[a]["winner"], "skill") for r in three]),
                                 mean([side(r[b]["winner"], "tools") for r in three]),
                                 mean([side(r[c]["winner"], "skill") for r in three])) for a, b, c in judges}
                row["reading"] = reads.pop() if len(reads) == 1 else "mixed"
    if len(models) > 1:
        tiers = json.load(open(os.path.join(ROOT, "model-routing.json"), encoding="utf-8"))["skills"]
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
    for m, d in summary["models"].items():
        kinds = d.get("by_kind", {})
        if len(kinds) == 2:
            lines += ["", f"**By who wrote the eval** (`{m}`):", "",
                      "| Evals | Count | Assertions met, skill | Baseline | Preferred blind | Second judge |",
                      "|---|---|---|---|---|---|"]
            for kind, name in (("author", "written by the skill's author"), ("held_out", "written without seeing the skill")):
                k = kinds[kind]
                lines.append(f"| {name} | {k['evals']} | {pct(k['skill'])} | {pct(k['baseline'])} | "
                             f"{pct(k['win'])}{ci(k['win_ci'])} | {pct(k.get('win2'))}{ci(k.get('win2_ci'))} |")
    for m, d in summary["models"].items():
        if d.get("second_judge"):
            lines += ["", f"**Second judge** `{d['second_judge']}` on `{m}`: preferred the skill's result in "
                      f"{pct(d['win2'])}{ci(d['win2_ci'])} of pairs, and picked the same side as the first judge in "
                      f"{d['judges_agree']} of {d['judges_decided']} pairs where both chose one."]
    for m, d in summary["models"].items():
        t = d.get("tools")
        if not t:
            continue
        lines += ["", f"## The scripts without the instructions (`{m}`)", "",
                  f"For the {t['skills']} skill(s) here that ship scripts, a third arm got the skill's scripts and the "
                  "data they read, with no SKILL.md, reference or examples: only a generated list of the scripts and "
                  "each one's first docstring line. All three arms ran on the same "
                  f"{t['evals']} eval(s).", "",
                  "| | Skill | Scripts only | Plain agent |", "|---|---|---|---|",
                  f"| Assertions met | {pct(t['skill'])} | {pct(t['tools'])} | {pct(t['baseline'])} |",
                  f"| $ per run | ${t['cost_skill']:.4f} | ${t['cost_tools']:.4f} | ${t['cost_baseline']:.4f} |", "",
                  "| Blind pair | Judge 1 | Judge 2 |", "|---|---|---|"]
        for label, k in (("Skill preferred to the plain agent", "pairwise"),
                         ("Scripts only preferred to the plain agent", "tools_vs_baseline"),
                         ("Skill preferred to scripts only", "skill_vs_tools")):
            two = {"pairwise": "pairwise2"}.get(k, k + "2")
            lines.append(f"| {label} | {pct(t.get('win_' + k))}{ci(t.get('win_' + k + '_ci'))} | "
                         f"{pct(t.get('win_' + two))}{ci(t.get('win_' + two + '_ci'))} |")
        mine = [r for r in summary["skills"] if r["model"] == m and r.get("reading")]
        if mine:
            counts = {}
            for r in mine:
                counts[r["reading"]] = counts.get(r["reading"], 0) + 1
            lines += ["", "Per skill, from the blind pairs (every judge must agree, or it reads *mixed*): "
                      + ", ".join(f"{n} {k}" for k, n in sorted(counts.items(), key=lambda x: -x[1])) + ". "
                      "Each skill has a handful of evals, so a row is a lead to check against the outputs, "
                      "not a verdict.", "",
                      "| Skill | Evals | Met: skill / scripts / plain | Skill > plain | Scripts > plain | Skill > scripts | Reading |",
                      "|---|---|---|---|---|---|---|"]
            for r in sorted(mine, key=lambda r: (r["reading"], r["skill"])):
                j2 = lambda k: (" / " + pct(r[k + "2"])) if (k + "2") in r else ""
                lines.append(f"| `{r['skill']}` | {r['evals']} | {pct(r['skill_met'])} / {pct(r['tools_met'])} / "
                             f"{pct(r['baseline_met'])} | {pct(r['preferred'])}{j2('preferred')} | "
                             f"{pct(r['tools_preferred'])}{j2('tools_preferred')} | "
                             f"{pct(r['skill_over_tools'])}{j2('skill_over_tools')} | {r['reading']} |")
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
    routing = json.load(open(os.path.join(ROOT, "model-routing.json"), encoding="utf-8"))
    tiers = routing["providers"][routing["active_provider"]]["models"]
    models, labels = [], {}
    for name in [x.strip() for x in spec.split(",") if x.strip()]:
        m = tiers.get(name, name)
        if price(m) is None:
            sys.exit(f"no price for model {m!r}: add it to PRICES in run_bench.py, so the budget can be enforced")
        models.append(m)
        labels[m] = name if name in tiers else m
    return models, labels


def fixture_tokens(skill, eval_id):
    """Roughly how many tokens of input files a judge reads beside an output: the files the run
    leaves behind are shown to it, up to workspace_files' limits, and a git history up to 30,000
    characters."""
    d = fixtures(skill, eval_id)
    if not d:
        return 0
    chars = 0
    for base, _, names in os.walk(d):
        for n in names:
            if n != GIT_HISTORY:
                chars += os.path.getsize(os.path.join(base, n))
    hist = os.path.join(d, GIT_HISTORY)
    return (min(chars, 90000) + (min(3 * os.path.getsize(hist), 30000) if os.path.isfile(hist) else 0)) / 4


def estimate(units, floor_units, judge_model):
    """Rough dollars for the calls not yet cached: characters / 4 as tokens, an assumed 4,000
    output tokens per generation, and the input files every judge reads beside each output.
    Every pairing is counted once per judge. Printed as an estimate; the run bills from usage."""
    total, fresh = 0.0, 0
    judges = [price(judge_model)] + ([price(SECOND_JUDGE)] if SECOND_JUDGE else [])
    jin, jout = judges[0]
    for s, e, model, trial in units:
        md = open(os.path.join(catalog.skill_dir(s), "SKILL.md"), encoding="utf-8").read()
        pin, pout = price(model)
        seen = 4000 + fixture_tokens(s, e.get("id"))                # one output, with the files it left
        arms = arm_systems(s, md)
        for arm, system in arms:
            extra = ("tools/" + scripts_digest(s)) if arm == "tools" else None
            fresh += not os.path.exists(cache_path("gen", model, system, e["prompt"], trial, fixtures(s, e.get("id")), extra))
            total += ((len(system) + len(e["prompt"])) / 4 * pin + 4000 * pout) / 1e6
            total += ((seen + 500) * jin + 500 * jout) / 1e6         # assertion judge reads one output
        pairs = 3 if len(arms) == 3 else 1                          # with the tools arm: two more pairings
        for qin, qout in judges:
            total += pairs * ((2 * seen + len(e["prompt"]) / 4) * qin + 100 * qout) / 1e6
    total += len(floor_units) * (400 * jin + 500 * jout) / 1e6
    return total, fresh


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--skills", help="comma-separated skill names (default: all)")
    ap.add_argument("--held-out", action="store_true",
                    help="run only the evals flagged held_out, written without reading the skill")
    ap.add_argument("--evals", help="comma-separated eval ids to run within each skill, e.g. 6,7 for new held-out "
                    "evals only (default: all)")
    ap.add_argument("--models", default="standard",
                    help="comma-separated tiers from model-routing.json (light, standard, heavy) or model ids")
    ap.add_argument("--backend", choices=("api", "claude-cli"), default="api",
                    help="api needs ANTHROPIC_API_KEY; claude-cli runs each call through a signed-in `claude -p`")
    ap.add_argument("--judge-model", default=JUDGE_MODEL)
    ap.add_argument("--second-judge", metavar="MODEL",
                    help="also run the blind pairwise comparison with this model, and report how often the two judges agree")
    ap.add_argument("--trials", type=int, default=1, help="runs per eval per arm (default 1)")
    ap.add_argument("--budget", type=float, default=5.0, help="hard stop in USD for this run (default 5)")
    ap.add_argument("--tolerance", type=float, default=0.05,
                    help="routing check: a model within this of the best score counts as adequate (default 0.05)")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--no-floor", action="store_true", help="skip grading the non-answer")
    ap.add_argument("--tools-arm", action="store_true",
                    help="claude-cli only: for each skill that ships scripts, also run its scripts without its "
                         "instructions, and judge that arm against the plain agent and against the skill (RFC-0067)")
    ap.add_argument("--dry-run", action="store_true", help="count calls and estimate cost; spend nothing")
    ap.add_argument("--out", default="bench-results", help="directory for results.json and report.md")
    ap.add_argument("--publish", metavar="FILE",
                    help="also write the summary (no outputs) to FILE; docs/benchmarks/latest.json is what the site reads")
    a = ap.parse_args()

    global BACKEND, SECOND_JUDGE, TOOLS_ARM
    BACKEND, SECOND_JUDGE, TOOLS_ARM = a.backend, a.second_judge, a.tools_arm
    if TOOLS_ARM and BACKEND != "claude-cli":
        sys.exit("--tools-arm needs --backend claude-cli: through the API there are no tools to run the scripts with")
    if SECOND_JUDGE and price(SECOND_JUDGE) is None:
        sys.exit(f"no price for second judge {SECOND_JUDGE!r}: add it to PRICES in run_bench.py")
    all_skills = catalog.skills()
    skills = [s.strip() for s in a.skills.split(",")] if a.skills else all_skills
    unknown = [s for s in skills if s not in all_skills]
    if unknown:
        sys.exit(f"unknown skill(s): {', '.join(unknown)}")
    models, labels = resolve_models(a.models)
    if price(a.judge_model) is None:
        sys.exit(f"no price for judge model {a.judge_model!r}: add it to PRICES in run_bench.py")
    evals = [(s, e) for s in skills for e in (load(s, "evals.json") or {}).get("evals", [])]
    if a.held_out:
        evals = [(s, e) for s, e in evals if e.get("held_out")]
    if a.evals:
        ids = {i.strip() for i in a.evals.split(",")}
        evals = [(s, e) for s, e in evals if str(e.get("id")) in ids]
        if not evals:
            sys.exit(f"no eval with id {a.evals} in {', '.join(skills)}")
    units = [(s, e, m, t) for s, e in evals for m in models for t in range(a.trials)]
    floor_units = [] if a.no_floor else evals

    est, fresh = estimate(units, floor_units, a.judge_model)
    n_tools = sum(1 for u in units if TOOLS_ARM and BACKEND == "claude-cli" and has_scripts(u[0]))
    n_judges = 2 if SECOND_JUDGE else 1
    print(f"{len(evals)} eval(s) across {len(skills)} skill(s) x {len(models)} model(s) x {a.trials} trial(s): "
          f"{2 * len(units) + n_tools} generations ({fresh} not cached), {2 * len(units) + n_tools + len(floor_units)} "
          f"assertion gradings, {n_judges * (len(units) + 2 * n_tools)} pairwise judgements"
          f"{f' ({n_tools} run(s) with the scripts-only arm)' if TOOLS_ARM else ''}. Rough cost if nothing is cached: ${est:.2f}. "
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
    # RFC-0049: a session knows who is signed in, and a model will write that name into an
    # Author or contact field unasked. Count it per skill, and keep it out of what is saved.
    pats = privacy.matcher(privacy.terms())
    named = {}
    for r in rows:
        for arm, d in r.get("arms", {}).items():
            d["output"], n = privacy.redact(d.get("output", ""), pats)
            if n:
                named.setdefault(r["skill"], set()).add(arm)
                d["named_you"] = n
    summary = summarize(rows, floor, models, labels, a.tolerance)
    scripted = {s for s in skills if os.path.isdir(os.path.join(catalog.skill_dir(s), "scripts"))}
    md = report(summary, a.judge_model, a.trials, budget.spent, scripted)
    if named:
        md += ("\n**Named you:** %d run(s) wrote the signed-in account's name, email or organization into their output "
               "(replaced with [you] in results.json): %s.\n" % (
                   sum(1 for r in rows for d in r.get("arms", {}).values() if d.get("named_you")),
                   ", ".join("`%s` (%s)" % (k, ", ".join(sorted(v))) for k, v in sorted(named.items()))))
    os.makedirs(a.out, exist_ok=True)
    json.dump({"backend": BACKEND, "judge_model": a.judge_model, "models": models, "trials": a.trials, "spent": budget.spent,
               "summary": summary, "floor": floor, "runs": rows},
              open(os.path.join(a.out, "results.json"), "w", encoding="utf-8"), indent=2)
    open(os.path.join(a.out, "report.md"), "w", encoding="utf-8").write(md)
    if a.publish:
        if privacy.scan_text(json.dumps(summary), pats):
            sys.exit("not publishing: the summary contains your name, email or organization (RFC-0049)")
        os.makedirs(os.path.dirname(os.path.abspath(a.publish)), exist_ok=True)
        with open(a.publish, "w", encoding="utf-8") as f:
            json.dump({"date": time.strftime("%Y-%m-%d"), "backend": BACKEND, "judge_model": a.judge_model,
                       "trials": a.trials, "scripted": sorted(scripted), **summary}, f, indent=1)
            f.write("\n")
    print(md)
    step = os.environ.get("GITHUB_STEP_SUMMARY")
    if step:
        with open(step, "a", encoding="utf-8") as f:
            f.write(md)
    if budget.spent >= a.budget:
        print(f"stopped at the ${a.budget:.2f} budget; rerun with a higher --budget to finish (cached calls are free)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

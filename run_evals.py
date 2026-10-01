#!/usr/bin/env python3
"""Run the catalogue's evals against a live model and report — never gate.

Two kinds, matching the two files every skill ships:

  activation  evals/eval_queries.json. The model sees every skill's name and description
              (what an agent sees when it decides which skill to load) plus one query, and
              names the skill it would load. A should_trigger row passes when it picks this
              skill; a should_not row passes when it picks anything else. Cheap: one short
              call per query, with the catalogue listing cached.
  assertions  evals/evals.json (--assertions). The skill's SKILL.md is the system prompt,
              the eval prompt is the request, and a judge model checks each assertion
              against the output. Costs a generation plus a judgement per eval.

Writes a JSON result file and a markdown report (to $GITHUB_STEP_SUMMARY in Actions).
With no ANTHROPIC_API_KEY it prints a notice and exits 0, so forks and PRs stay green.

  python3 run_evals.py                          # activation, every skill
  python3 run_evals.py --skills doc-critique,adr-generator --assertions
"""
import argparse
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor

import catalog
from anthropic_api import APIError, api_key, messages

ROUTER_MODEL = "claude-haiku-4-5-20251001"
SKILL_MODEL = "claude-sonnet-5-5"
JUDGE_MODEL = "claude-sonnet-5-5"


def load(skill, name):
    p = os.path.join(catalog.skill_dir(skill), "evals", name)
    return json.load(open(p)) if os.path.exists(p) else None


def description(skill):
    return json.load(open(os.path.join(catalog.skill_dir(skill), "manifest.json")))["description"]


def router_prompt(all_skills):
    listing = "\n".join(f"- {s}: {description(s)}" for s in all_skills)
    return ("You decide which skill an AI coding agent should load for a user's request.\n\n"
            f"Available skills:\n{listing}\n\n"
            "Reply with exactly one skill name from the list — the one you would load to handle the "
            "request — or `none` if no skill fits. Reply with the name only, nothing else.")


def route(system, query, model):
    text, _ = messages(model, system, query, max_tokens=20, cache_system=True)
    return text.strip().strip("`").split()[0].lower() if text.strip() else "none"


def activation(skills, all_skills, model, workers):
    system = router_prompt(all_skills)
    jobs = [(s, q) for s in skills for q in (load(s, "eval_queries.json") or [])]

    def run(job):
        s, q = job
        try:
            picked = route(system, q["query"], model)
        except APIError as e:
            return {"skill": s, "query": q["query"], "should_trigger": q["should_trigger"], "error": str(e)}
        ok = (picked == s) == bool(q["should_trigger"])
        return {"skill": s, "query": q["query"], "should_trigger": q["should_trigger"], "picked": picked, "pass": ok}

    with ThreadPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(run, jobs))


JUDGE_SYSTEM = ("You grade an AI assistant's output against a list of assertions. Judge each assertion "
                "strictly from the output text: pass only if the output clearly satisfies it. Reply with "
                "JSON only: [{\"n\": 1, \"pass\": true, \"why\": \"<one short sentence>\"}, ...]")


def assertions(skills, skill_model, judge_model, workers):
    jobs = []
    for s in skills:
        doc = load(s, "evals.json") or {}
        md = open(os.path.join(catalog.skill_dir(s), "SKILL.md")).read()
        for e in doc.get("evals", []):
            jobs.append((s, md, e))

    def run(job):
        s, md, e = job
        system = (md + "\n\n---\nThis is a non-interactive run: the user cannot answer follow-up "
                  "questions. Work with what the request gives you, following the skill's rules for "
                  "non-interactive runs.")
        try:
            out, _ = messages(skill_model, system, e["prompt"], max_tokens=8000)
            numbered = "\n".join(f"{i}. {a}" for i, a in enumerate(e["assertions"], 1))
            verdict, _ = messages(judge_model, JUDGE_SYSTEM,
                                  f"<output>\n{out}\n</output>\n\n<assertions>\n{numbered}\n</assertions>",
                                  max_tokens=2000)
            m = re.search(r"\[.*\]", verdict, re.S)
            grades = json.loads(m.group(0)) if m else []
        except (APIError, json.JSONDecodeError) as err:
            return {"skill": s, "id": e.get("id"), "error": str(err)}
        by_n = {g.get("n"): g for g in grades if isinstance(g, dict)}
        rows = [{"assertion": a, "pass": bool(by_n.get(i, {}).get("pass")), "why": by_n.get(i, {}).get("why", "not graded")}
                for i, a in enumerate(e["assertions"], 1)]
        return {"skill": s, "id": e.get("id"), "assertions": rows}

    with ThreadPoolExecutor(max_workers=max(1, workers // 2)) as ex:
        return list(ex.map(run, jobs))


def pct(a, b):
    return f"{100 * a / b:.0f}%" if b else "–"


def report(act, asr, model):
    lines = ["# Skill evals (report-only)", ""]
    if act:
        done = [r for r in act if "pass" in r]
        errs = [r for r in act if "error" in r]
        pos = [r for r in done if r["should_trigger"]]
        neg = [r for r in done if not r["should_trigger"]]
        lines += [f"## Activation — {model}", "",
                  f"**{sum(r['pass'] for r in done)}/{len(done)} queries routed as intended** · "
                  f"triggers when it should: {pct(sum(r['pass'] for r in pos), len(pos))} · "
                  f"stays quiet when it should: {pct(sum(r['pass'] for r in neg), len(neg))}"
                  + (f" · {len(errs)} API error(s)" if errs else ""), ""]
        misses = [r for r in done if not r["pass"]]
        if misses:
            lines += ["| Skill | Query | Expected | Model picked |", "|---|---|---|---|"]
            for r in sorted(misses, key=lambda r: r["skill"]):
                exp = "this skill" if r["should_trigger"] else "another skill"
                lines.append(f"| `{r['skill']}` | {r['query'].replace('|', '/')} | {exp} | `{r['picked']}` |")
            lines.append("")
    if asr:
        graded = [r for r in asr if "assertions" in r]
        total = sum(len(r["assertions"]) for r in graded)
        passed = sum(a["pass"] for r in graded for a in r["assertions"])
        lines += ["## Assertions", "", f"**{passed}/{total} assertions met** across {len(graded)} eval(s)"
                  + (f" · {len(asr) - len(graded)} error(s)" if len(graded) < len(asr) else ""), "",
                  "| Skill | Eval | Met | Missed |", "|---|---|---|---|"]
        for r in sorted(graded, key=lambda r: r["skill"]):
            miss = [a["assertion"] for a in r["assertions"] if not a["pass"]]
            lines.append(f"| `{r['skill']}` | {r['id']} | {len(r['assertions']) - len(miss)}/{len(r['assertions'])} | "
                         + ("<br>".join(m.replace("|", "/") for m in miss) or "–") + " |")
        lines.append("")
    lines.append("A miss is a prompt to look, not a verdict: models vary run to run, and the router here "
                 "approximates how each tool picks a skill.")
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--skills", help="comma-separated skill names (default: all)")
    ap.add_argument("--assertions", action="store_true", help="also run evals.json through the skill and a judge")
    ap.add_argument("--no-activation", action="store_true", help="skip the trigger-query run")
    ap.add_argument("--model", default=ROUTER_MODEL, help=f"router model (default {ROUTER_MODEL})")
    ap.add_argument("--skill-model", default=SKILL_MODEL)
    ap.add_argument("--judge-model", default=JUDGE_MODEL)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--out", default="evals-results.json")
    a = ap.parse_args()

    if not api_key():
        print("::notice::ANTHROPIC_API_KEY is not set — skipping the eval run. "
              "Add it as a repository secret to turn the weekly evals on.")
        return 0
    all_skills = catalog.skills()
    skills = [s.strip() for s in a.skills.split(",")] if a.skills else all_skills
    unknown = [s for s in skills if s not in all_skills]
    if unknown:
        sys.exit(f"unknown skill(s): {', '.join(unknown)}")

    act = [] if a.no_activation else activation(skills, all_skills, a.model, a.workers)
    asr = assertions(skills, a.skill_model, a.judge_model, a.workers) if a.assertions else []
    json.dump({"router_model": a.model, "activation": act, "assertions": asr}, open(a.out, "w"), indent=2)
    md = report(act, asr, a.model)
    print(md)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a") as f:
            f.write(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())

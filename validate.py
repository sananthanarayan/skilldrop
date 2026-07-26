#!/usr/bin/env python3
"""Consistency lint for skilldrop. No deps, no network. Run from the repo root:

    python3 validate.py            # exit 0 = clean, 1 = failures
    python3 validate.py --quiet    # failures only, no warnings

Checks (FAIL):
  - folder name == SKILL.md frontmatter `name` == manifest.json `name`
  - manifest has all required fields (name, version, description, entrypoint,
    deps, env, related, tags, model)
  - manifest `model.tier` == model-routing.json tier, both directions
  - manifest `related`: every entry is a real skill folder, and every sibling
    skill referenced in SKILL.md (backticked) appears in `related` — and vice versa
  - evals/ files, when present, parse and have the right shape: evals.json has
    >=1 eval with prompt + assertions; eval_queries.json has both should_trigger
    true and false rows
  - manifest description == SKILL.md frontmatter description (whitespace-normalized)
  - packs.json: every pack entry is a real skill folder, and every skill
    belongs to at least one pack
  - manifest hooks (optional): each entry's event is in the RFC-0006 vocabulary,
    its action is a real skill folder, and it carries a description
  - README.md skill counts match the number of skills on disk (prose drifts; the
    generated catalogue site cannot, so only the hand-written numbers need checking)
  - agents/<name>.md: filename == frontmatter `name`, and `description` is present
  - every `<name>` subagent a SKILL.md delegates to is a real file in agents/

Warnings (non-fatal):
  - SKILL.md over ~500 lines (golden rule 3)
  - agents/<name>.md missing the recommended `tools` or `model` frontmatter
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SKILLS = os.path.join(ROOT, "skills")
AGENTS = os.path.join(ROOT, "agents")
REQUIRED_FIELDS = ["name", "version", "description", "entrypoint", "deps", "env", "related", "tags", "model"]
HOOK_EVENTS = {"session-start", "pre-commit-review", "on-demand"}  # RFC-0006; kept in sync with bin/skilldrop.js

failures, warnings = [], []


def fail(skill, msg):
    failures.append(f"{skill}: {msg}")


def warn(skill, msg):
    warnings.append(f"{skill}: {msg}")


SUBAGENT_REF = re.compile(r"`([a-z0-9][a-z0-9-]*)`\s+subagent")


def check_agents(skill_dirs):
    """agents/ is the repo's second primitive and had no enforced invariants at all.
    The link a skill declares to a subagent is real — feature-implement-loop delegates
    to `devils-advocate` — so a rename that misses one silently breaks the delegation."""
    if not os.path.isdir(AGENTS):
        return set()
    names = set()
    for f in sorted(os.listdir(AGENTS)):
        if not f.endswith(".md") or f == "README.md":
            continue
        stem = f[:-3]
        names.add(stem)
        fm = frontmatter(open(os.path.join(AGENTS, f), encoding="utf-8").read())
        fields = dict(re.findall(r"^([a-z-]+):\s*(.+?)\s*$", fm, re.M))
        if fields.get("name") != stem:
            fail(f"agents/{f}", f"frontmatter name '{fields.get('name')}' != filename '{stem}'")
        if not fields.get("description"):
            fail(f"agents/{f}", "missing `description` — it is what routes a delegation here")
        for k in ("tools", "model"):
            if k not in fields:
                warn(f"agents/{f}", f"no `{k}` in frontmatter (recommended)")

    for d in skill_dirs:
        sp = os.path.join(SKILLS, d, "SKILL.md")
        if not os.path.exists(sp):
            continue
        for ref in set(SUBAGENT_REF.findall(open(sp, encoding="utf-8").read())):
            if ref not in names:
                fail(d, f"SKILL.md delegates to the `{ref}` subagent, but agents/{ref}.md does not exist")
    return names


def frontmatter(md_text):
    parts = md_text.split("---")
    return parts[1] if len(parts) >= 3 else ""


def main():
    routing = json.load(open(os.path.join(ROOT, "model-routing.json")))["skills"]
    skill_dirs = sorted(d for d in os.listdir(SKILLS) if os.path.isdir(os.path.join(SKILLS, d)))
    dir_set = set(skill_dirs)

    for d in skill_dirs:
        p = os.path.join(SKILLS, d)
        try:
            manifest = json.load(open(os.path.join(p, "manifest.json")))
        except (OSError, json.JSONDecodeError) as e:
            fail(d, f"manifest.json unreadable: {e}")
            continue
        try:
            md = open(os.path.join(p, "SKILL.md")).read()
        except OSError:
            fail(d, "SKILL.md missing")
            continue

        fm = frontmatter(md)
        m_name = re.search(r"^name:\s*(\S+)", fm, re.M)
        if not m_name or not (d == manifest.get("name") == m_name.group(1)):
            fail(d, f"name triple mismatch: folder={d} manifest={manifest.get('name')} "
                    f"frontmatter={m_name.group(1) if m_name else None}")

        for field in REQUIRED_FIELDS:
            if field not in manifest:
                fail(d, f"manifest missing required field '{field}'")

        tier = manifest.get("model", {}).get("tier")
        if d not in routing:
            fail(d, "no entry in model-routing.json")
        elif tier != routing[d].get("tier"):
            fail(d, f"tier mismatch: manifest={tier} routing={routing[d].get('tier')}")

        refs = {r for r in re.findall(r"`([a-z][a-z0-9-]+)`", md) if r in dir_set and r != d}
        related = manifest.get("related")
        if isinstance(related, list):
            rel_set = set(related)
            for r in rel_set - dir_set:
                fail(d, f"related entry '{r}' is not a skill folder")
            for r in sorted(refs - rel_set):
                fail(d, f"SKILL.md references `{r}` but manifest related omits it")
            for r in sorted(rel_set & dir_set - refs):
                fail(d, f"manifest related lists '{r}' but SKILL.md never references it")
        elif related is not None:
            fail(d, "related must be a flat list of skill names")

        for h in manifest.get("hooks", []) or []:
            if not isinstance(h, dict):
                fail(d, "each hooks entry must be an object with event/action/description")
                continue
            if h.get("event") not in HOOK_EVENTS:
                fail(d, f"hook event {h.get('event')!r} not in {sorted(HOOK_EVENTS)}")
            if h.get("action") not in dir_set:
                fail(d, f"hook action {h.get('action')!r} is not a skill folder")
            if not h.get("description"):
                fail(d, f"hook for event {h.get('event')!r} needs a description")

        evals_path = os.path.join(p, "evals", "evals.json")
        queries_path = os.path.join(p, "evals", "eval_queries.json")
        if os.path.exists(evals_path):
            try:
                ev = json.load(open(evals_path))
                if ev.get("skill_name") != d:
                    fail(d, f"evals.json skill_name={ev.get('skill_name')} != {d}")
                if not ev.get("evals") or any(not e.get("prompt") or not e.get("assertions") for e in ev["evals"]):
                    fail(d, "evals.json needs >=1 eval, each with prompt + assertions")
            except json.JSONDecodeError as e:
                fail(d, f"evals.json invalid JSON: {e}")
        if os.path.exists(queries_path):
            try:
                qs = json.load(open(queries_path))
                flags = {q.get("should_trigger") for q in qs}
                if flags != {True, False}:
                    fail(d, "eval_queries.json needs both should_trigger true and false rows")
            except json.JSONDecodeError as e:
                fail(d, f"eval_queries.json invalid JSON: {e}")

        n_lines = md.count("\n") + 1
        if n_lines > 500:
            warn(d, f"SKILL.md is {n_lines} lines (golden rule: ~500 max)")

        m_desc = re.search(r"^description:\s*(.+?)(?=^\w+:|\Z)", fm, re.M | re.S)
        if m_desc and " ".join(m_desc.group(1).split()) != " ".join(manifest.get("description", "").split()):
            fail(d, "manifest description differs from SKILL.md frontmatter description")

    for r in sorted(set(routing) - dir_set):
        fail("model-routing.json", f"entry '{r}' has no skill folder")

    packs = json.load(open(os.path.join(ROOT, "packs.json")))["packs"]
    packed = set()
    for pname, pack in packs.items():
        for s in pack.get("skills", []):
            if s not in dir_set:
                fail("packs.json", f"pack '{pname}' lists '{s}', which is not a skill folder")
            packed.add(s)
    for s in sorted(dir_set - packed):
        fail("packs.json", f"skill '{s}' belongs to no pack — every skill needs an audience")

    agent_names = check_agents(skill_dirs)

    # The site regenerates its counts from the manifests; README prose does not.
    # This is the only place a skill count can go stale unnoticed (RFC-0011).
    readme = open(os.path.join(ROOT, "README.md"), encoding="utf-8").read()
    for n in set(re.findall(r"\b(\d{2})\s+(?:portable |)(?:AI-agent |)skills\b", readme)):
        if int(n) != len(skill_dirs):
            fail("README.md", f"says '{n} skills' but {len(skill_dirs)} are on disk")

    quiet = "--quiet" in sys.argv
    if warnings and not quiet:
        print(f"-- {len(warnings)} warning(s) --")
        for w in warnings:
            print("  WARN", w)
    if failures:
        print(f"-- {len(failures)} FAILURE(s) --")
        for f in failures:
            print("  FAIL", f)
        sys.exit(1)
    print(f"OK: {len(skill_dirs)} skills + {len(agent_names)} agents validated"
          + ("" if quiet else f", {len(warnings)} warning(s)"))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Run one skill against an input through the Anthropic API — the engine behind action.yml.

The skill's SKILL.md becomes the system prompt, with the text files it links (reference.md,
templates/, rubrics/, lenses/, examples/) inlined after it, so the model has what the skill
would read. Nothing in the skill is executed: where a skill says to run a script, the model is
told it can't, and does the reasoning by hand or names the command to run.

Inputs come from environment variables (how the composite action passes them, so no workflow
expression is ever interpolated into a shell line) or the matching flags:

  SKILL         skill name (required)
  INPUT         the request text
  INPUT_FILE    a file whose contents are appended to the request
  DIFF_BASE     a git ref; `git diff <ref>...HEAD` is appended (e.g. origin/main on a PR)
  CATALOG       where to find the skill: a skilldrop catalog (packs/ or skills/) or any folder
                holding <skill>/SKILL.md (default: this repo)
  MODEL         default claude-sonnet-5-5
  MAX_TOKENS    default 8000
  FAIL_ON       a regex; if the output matches, exit 1 (e.g. "MAJOR REWRITE|BLOCKED")
  OUTPUT_FILE   where to write the output (default skill-output.md)
"""
import argparse
import glob
import os
import re
import subprocess
import sys

from anthropic_api import APIError, messages

HERE = os.path.dirname(os.path.abspath(__file__))
INLINE_DIRS = ("templates", "rubrics", "lenses", "references", "examples")
TEXT_EXT = {".md", ".json", ".yaml", ".yml", ".txt", ".toml", ".csv", ".mmd"}
INLINE_BUDGET = 200_000  # characters of sibling material; SKILL.md itself is always sent


def find_skill(catalog, name):
    pats = [f"packs/*/skills/{name}/SKILL.md", f"skills/{name}/SKILL.md", f".claude/skills/{name}/SKILL.md",
            f".agents/skills/{name}/SKILL.md", f"{name}/SKILL.md", "SKILL.md"]
    for p in pats:
        hits = sorted(glob.glob(os.path.join(catalog, p)))
        for h in hits:
            if p != "SKILL.md" or os.path.basename(os.path.dirname(os.path.abspath(h))) == name:
                return os.path.dirname(h)
    return None


def skill_system(sdir):
    md = open(os.path.join(sdir, "SKILL.md"), encoding="utf8").read()
    parts, used = [md], 0
    files = [os.path.join(sdir, "reference.md")] if os.path.exists(os.path.join(sdir, "reference.md")) else []
    for d in INLINE_DIRS:
        for root, _, names in os.walk(os.path.join(sdir, d)):
            files += [os.path.join(root, n) for n in sorted(names) if os.path.splitext(n)[1] in TEXT_EXT]
    skipped = []
    for f in files:
        body = open(f, encoding="utf8", errors="replace").read()
        rel = os.path.relpath(f, sdir)
        if used + len(body) > INLINE_BUDGET:
            skipped.append(rel)
            continue
        used += len(body)
        parts.append(f"\n\n<file path=\"{rel}\">\n{body}\n</file>")
    parts.append("\n\n---\nYou are running inside CI, non-interactively: nobody can answer a follow-up "
                 "question, so follow the skill's rules for non-interactive runs. You cannot execute "
                 "scripts or read files beyond those included above; where the skill says to run a "
                 "script, do the reasoning it describes by hand and say which command the user should run.")
    return "".join(parts), skipped


def main():
    env = os.environ.get
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--skill", default=env("SKILL", ""))
    ap.add_argument("--input", default=env("INPUT", ""))
    ap.add_argument("--input-file", default=env("INPUT_FILE", ""))
    ap.add_argument("--diff-base", default=env("DIFF_BASE", ""))
    ap.add_argument("--catalog", default=env("CATALOG", "") or HERE)
    ap.add_argument("--model", default=env("MODEL", "") or "claude-sonnet-5-5")
    ap.add_argument("--max-tokens", type=int, default=int(env("MAX_TOKENS", "") or 8000))
    ap.add_argument("--fail-on", default=env("FAIL_ON", ""))
    ap.add_argument("--output-file", default=env("OUTPUT_FILE", "") or "skill-output.md")
    a = ap.parse_args()

    if not a.skill:
        sys.exit("error: no skill named — set the `skill` input")
    sdir = find_skill(a.catalog, a.skill)
    if not sdir:
        sys.exit(f"error: no {a.skill}/SKILL.md under {a.catalog}")
    request = a.input.strip()
    if a.input_file:
        request += f"\n\n<file path=\"{a.input_file}\">\n{open(a.input_file, encoding='utf8', errors='replace').read()}\n</file>"
    if a.diff_base:
        try:
            diff = subprocess.run(["git", "diff", f"{a.diff_base}...HEAD"], check=True,
                                  capture_output=True, text=True).stdout
        except (OSError, subprocess.CalledProcessError) as e:
            sys.exit(f"error: git diff {a.diff_base}...HEAD failed — check out with fetch-depth: 0 ({e})")
        request += f"\n\n<diff base=\"{a.diff_base}\">\n{diff}\n</diff>"
    if not request.strip():
        sys.exit("error: nothing to run the skill on — set `input`, `input-file` or `diff-base`")

    system, skipped = skill_system(sdir)
    try:
        out, usage = messages(a.model, system, request, max_tokens=a.max_tokens)
    except APIError as e:
        sys.exit(f"error: {e}")
    with open(a.output_file, "w", encoding="utf8") as f:
        f.write(out)

    matched = bool(a.fail_on) and re.search(a.fail_on, out) is not None
    summary = env("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf8") as f:
            f.write(f"## skilldrop: `{a.skill}`\n\n{out}\n\n---\n<sub>{a.model} · "
                    f"{usage.get('input_tokens', '?')} in / {usage.get('output_tokens', '?')} out"
                    + (f" · fail-on `{a.fail_on}` matched" if matched else "") + "</sub>\n")
    gh_out = env("GITHUB_OUTPUT")
    if gh_out:
        with open(gh_out, "a", encoding="utf8") as f:
            f.write(f"output-file={a.output_file}\nfailed={'true' if matched else 'false'}\n")
    print(out)
    if skipped:
        print(f"\n(note: {len(skipped)} reference file(s) left out to fit the budget: {', '.join(skipped)})", file=sys.stderr)
    if matched:
        print(f"::error::{a.skill} output matched fail-on pattern '{a.fail_on}'")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

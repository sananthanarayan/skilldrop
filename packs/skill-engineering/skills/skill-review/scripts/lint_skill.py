#!/usr/bin/env python3
"""lint_skill.py - check the mechanical parts of an Agent Skill folder.

Usage:
    python3 lint_skill.py <skill-dir> [--siblings <dir>] [--json] [-o <report-path>]

Checks a folder that holds a SKILL.md (Claude Code, Codex, Copilot, Cursor, Kiro,
Antigravity all read the same shape):

  frontmatter   SKILL.md opens with a --- block holding `name` and `description`
  name          kebab-case, at most 64 characters, equal to the folder name
  description   1-1024 characters, long enough for a router to act on, ends with
                trigger phrases ("Use when ...")
  paths         every relative link and in-skill path (scripts/, references/,
                templates/, examples/, assets/, lenses/, rubrics/) named in SKILL.md exists
  portability   every ${CLAUDE_SKILL_DIR}/x also appears as a plain relative x;
                no absolute home-directory paths
  structure     SKILL.md line count, a quality bar, anti-patterns, a when-not-to-use
                section, reference files nobody links, scripts nobody calls
  evals         evals/evals.json and evals/eval_queries.json present and well formed
  safety        the same pattern families `skilldrop scan` uses: prose instructions to
                override, conceal, rewrite memory, send data out or fetch remote
                instructions; script patterns for remote exec, shell, network,
                credentials, and deletes outside the skill
  siblings      (with --siblings) a duplicate name, or a description that overlaps
                heavily with another skill's

Every finding is ERROR (breaks loading or a promise the skill makes), WARN (a reviewer
should look), or INFO. Exit code: 0 no errors, 1 at least one ERROR, 2 bad input.
Stdlib only, Python 3.9+, no network.
"""

import argparse
import json
import os
import re
import sys

MAX_NAME = 64
MAX_DESC = 1024
MIN_DESC = 120
MAX_LINES = 500
# Word-overlap (Jaccard) of two descriptions' content words. Across the 60-odd skilldrop
# skills the closest distinct pair scores 0.16, so 0.20 flags a real collision, not a cousin.
OVERLAP_WARN = 0.20

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
FENCE_RE = re.compile(r"^```.*?^```", re.M | re.S)
MD_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
INSKILL_RE = re.compile(
    r"(?<![\w/.$}])((?:scripts|references|templates|examples|assets|lenses|rubrics)/[\w./<>{}*-]+)")
SKILL_DIR_RE = re.compile(r"\$\{?CLAUDE_SKILL_DIR\}?/([\w./<>{}*-]+)")
TRIGGER_RE = re.compile(
    r"\b(use (it |this skill |this )?(when|whenever|for|if|to)|trigger(s|ed)? (on|when)|"
    r"invoke when|when the user|says \")", re.I)
WEAK_OPENING_RE = re.compile(r"^(this skill|a skill|skill (that|for|to)|helps?\b|i\b|an? (helpful|useful|simple|powerful))", re.I)
ABS_PATH_RE = re.compile(r"(?<![\w~])(/Users/[A-Za-z0-9._-]+/|/home/[A-Za-z0-9._-]+/|[A-Z]:\\\\?Users\\\\?)")
MATERIAL_DIRS = ("references", "lenses", "rubrics")
SCRIPT_EXT = {".py", ".js", ".mjs", ".cjs", ".sh", ".bash", ".zsh", ".rb", ".pl", ".ps1"}

# The pattern families below mirror `skilldrop scan` (bin/skilldrop.js, RFC-0022) so a
# skill reviewed outside the skilldrop repo gets the same first pass. Literals are split
# with character classes so this file does not match its own rules.
PROSE_RULES = [
    ("instruction-override", "ERROR", "AST01, LLM01", "tells the agent to discard its earlier instructions",
     re.compile(r"ignor[e]\s+(all\s+)?(previous|prior|earlier|above|preceding)\s+(instructions|prompts|rules)", re.I)),
    ("conceal-from-user", "ERROR", "AST01, LLM01", "tells the agent to hide actions from the user",
     re.compile(r"(do\s*n[o']?t|never|without)\s+(tell|telling|inform|informing|notify|notifying|mention|mentioning)\s+(the\s+)?(use[r]|huma[n])", re.I)),
    ("memory-overwrite", "ERROR", "AST01, LLM01", "tells the agent to rewrite its own memory or policy file",
     re.compile(r"(update|overwrite|append\s+to|modify)\s+your\s+(own\s+)?(SOUL|MEMORY|CLAUDE|AGENTS)\.m[d]", re.I)),
    ("prose-exfil", "WARN", "AST01, LLM02", "tells the agent to send data to an external endpoint",
     re.compile(r"\b(POST|send|upload|transmit)\b[^\n.]{0,60}\bto\s+http[s]?://", re.I)),
    ("remote-instructions", "WARN", "AST05, LLM01",
     "tells the agent to fetch instructions from a URL at run time; what it obeys can change after review",
     re.compile(r"\b(fetch|download|load|read|follow|pull)\b[^\n.]{0,40}\b(instructions|rules|prompt|system prompt|skill|directives)\b[^\n.]{0,30}\bfrom\s+(http[s]?://|<?url)", re.I)),
]

SCRIPT_RULES = [
    ("exec-remote", "ERROR", "AST01, AST02", "downloads and executes remote content",
     re.compile(r"(cur[l]|wge[t])[^\n|]*\|\s*(sudo\s+)?(ba|z|)s[h]\b|eva[l]\s*\(\s*(requests|urllib|fetch)|base64\s+(-d|--decode)[^\n|]*\|\s*(ba|z|)s[h]\b", re.I)),
    ("shell-exec", "WARN", "AST03, LLM06", "executes shell commands",
     re.compile(r"\b(os\.syste[m]|subproces[s]\.(run|call|Popen|check_output)|child_proces[s]|execSyn[c]|spawnSyn[c]|shell_exe[c])")),
    ("network", "WARN", "AST03, LLM02", "makes outbound network calls",
     re.compile(r"\b(request[s]\.(get|post|put)|urlli[b]\.request|http[x]\.|axio[s]\.|node-fetc[h]|\bfetc[h]\s*\(\s*[\"'`]https?:|cur[l]\s+https?:|wge[t]\s+https?:)", re.I)),
    ("credentials", "WARN", "AST01, LLM02", "reads credentials or secret material",
     re.compile(r"\b(os\.enviro[n]|process\.en[v])\b[^\n]{0,40}(TOKEN|KEY|SECRET|PASSWORD|CREDENTIAL)|~/\.(aws|ssh|npmrc|netrc)\b|\.en[v]\b|id_rs[a]", re.I)),
    ("broad-fs", "INFO", "AST03, LLM06", "deletes or writes outside the skill's own folder",
     re.compile(r"\b(shuti[l]\.rmtree|r[m]\s+-rf\s+[~/]|ope[n]\s*\(\s*[\"'`]/(etc|usr|bin)|fs\.(unlink|rmSync)\s*\([^)]*\.\./)")),
]

STOPWORDS = set("""a an and are as at be by for from has have in into is it its of on or that the
their them this to use used user users when whenever which with without your you skill skills
says want wants wanted needs need like also each every over under than then only just one
any all not no can will should would could about across after before more most other such""".split())


class Report(object):
    def __init__(self, skill_dir):
        self.skill_dir = skill_dir
        self.findings = []
        self.facts = {}

    def add(self, level, area, msg, where=""):
        self.findings.append({"level": level, "area": area, "message": msg, "where": where})

    def count(self, level):
        return sum(1 for f in self.findings if f["level"] == level)


def die(msg):
    sys.stderr.write("lint_skill: " + msg + "\n")
    sys.exit(2)


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def split_frontmatter(text):
    """Return (frontmatter_text or None, body, body_start_line)."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, text, 1
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return "\n".join(lines[1:i]), "\n".join(lines[i + 1:]), i + 2
    return None, text, 1


def parse_frontmatter(fm):
    """Minimal YAML subset: top-level `key: value`, folded/literal blocks, quoted strings."""
    out = {}
    lines = fm.splitlines()
    i = 0
    while i < len(lines):
        m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", lines[i])
        if not m:
            i += 1
            continue
        key, val = m.group(1), m.group(2).strip()
        i += 1
        cont = []
        while i < len(lines) and (lines[i].startswith((" ", "\t")) or not lines[i].strip()):
            cont.append(lines[i].strip())
            i += 1
        if val in (">", "|", ">-", "|-", ">+", "|+"):
            val = " ".join(c for c in cont if c)
        elif cont and not val.startswith(("[", "{")):
            val = " ".join([val] + [c for c in cont if c])
        if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
            val = val[1:-1]
        out[key] = val
    return out


def content_words(text):
    return set(w for w in re.findall(r"[a-z][a-z0-9-]{3,}", text.lower()) if w not in STOPWORDS)


def check_frontmatter(rep, folder, text):
    fm, body, _ = split_frontmatter(text)
    if fm is None:
        rep.add("ERROR", "frontmatter", "SKILL.md does not open with a --- frontmatter block; no tool will load it", "SKILL.md:1")
        return {}, body
    meta = parse_frontmatter(fm)
    name = meta.get("name", "")
    if not name:
        rep.add("ERROR", "frontmatter", "frontmatter has no `name`", "SKILL.md")
    else:
        if name != folder:
            rep.add("ERROR", "frontmatter", "name '%s' does not match folder '%s'; tools key the skill on both" % (name, folder), "SKILL.md")
        if not NAME_RE.match(name):
            rep.add("ERROR", "frontmatter", "name '%s' is not kebab-case (lowercase letters, digits, single hyphens)" % name, "SKILL.md")
        if len(name) > MAX_NAME:
            rep.add("ERROR", "frontmatter", "name is %d characters; the limit is %d" % (len(name), MAX_NAME), "SKILL.md")
    desc = meta.get("description", "")
    rep.facts["description_chars"] = len(desc)
    if not desc:
        rep.add("ERROR", "description", "frontmatter has no `description`; a router has nothing to match on", "SKILL.md")
    else:
        if len(desc) > MAX_DESC:
            rep.add("ERROR", "description", "description is %d characters; the limit is %d" % (len(desc), MAX_DESC), "SKILL.md")
        elif len(desc) < MIN_DESC:
            rep.add("WARN", "description", "description is %d characters; under %d rarely names both the artifact and the triggers" % (len(desc), MIN_DESC), "SKILL.md")
        if not TRIGGER_RE.search(desc):
            rep.add("WARN", "description", "description has no trigger phrases (\"Use when the user ...\", \"says ...\"); routing will rely on luck", "SKILL.md")
        elif TRIGGER_RE.search(desc).start() < len(desc) * 0.25:
            rep.add("INFO", "description", "trigger phrases come before the artifact; lead with what the skill produces", "SKILL.md")
        if WEAK_OPENING_RE.match(desc):
            rep.add("WARN", "description", "description opens with filler (\"%s...\"); open with the artifact it produces" % desc[:24], "SKILL.md")
    for key in meta:
        if key not in ("name", "description", "license", "compatibility", "metadata", "allowed-tools",
                       "version", "disable-model-invocation", "user-invocable", "argument-hint", "model"):
            rep.add("INFO", "frontmatter", "frontmatter key '%s' is not one the common tools read; check it is intended" % key, "SKILL.md")
    return meta, body


def is_placeholder(target):
    return "..." in target or "…" in target or any(c in target for c in "{}<>*")


def check_paths(rep, skill_dir, text):
    prose = FENCE_RE.sub("", text)
    seen = set()
    for m in MD_LINK_RE.finditer(prose):
        target = m.group(1).split("#")[0]
        if not target or re.match(r"^[a-z]+:", target) or target.startswith("/") or is_placeholder(target):
            continue
        seen.add(target)
        if not os.path.exists(os.path.normpath(os.path.join(skill_dir, target))):
            rep.add("ERROR", "paths", "link target '%s' does not exist" % target, "SKILL.md")
    for m in INSKILL_RE.finditer(prose):
        rel = m.group(1).rstrip(".,)`'\"")
        if rel in seen or is_placeholder(rel):
            continue
        seen.add(rel)
        if not os.path.exists(os.path.join(skill_dir, rel)):
            rep.add("ERROR", "paths", "SKILL.md names '%s' but it does not exist in the skill" % rel, "SKILL.md")
    # ${CLAUDE_SKILL_DIR} paths are checked everywhere, fences included: that is where commands live.
    for m in SKILL_DIR_RE.finditer(text):
        rel = m.group(1).rstrip(".,)`'\"")
        if is_placeholder(rel) or rel in seen:
            continue
        seen.add(rel)
        if not os.path.exists(os.path.join(skill_dir, rel)):
            rep.add("ERROR", "paths", "${CLAUDE_SKILL_DIR}/%s does not exist in the skill" % rel, "SKILL.md")


def check_portability(rep, skill_dir, text):
    claude_refs = set(m.group(1).rstrip(".,)`'\"") for m in SKILL_DIR_RE.finditer(text))
    stripped = SKILL_DIR_RE.sub("", text)
    for rel in sorted(claude_refs):
        if is_placeholder(rel):
            continue
        if not re.search(r"(?<![\w/}])" + re.escape(rel), stripped):
            rep.add("ERROR", "portability",
                    "${CLAUDE_SKILL_DIR}/%s has no plain relative fallback; only Claude Code sets that variable, so Codex, Copilot, Cursor and Kiro cannot find the file" % rel,
                    "SKILL.md")
    for path, rel in iter_files(skill_dir, (".md",)):
        if rel.startswith("examples" + os.sep):
            continue  # examples illustrate; an absolute path there is not an instruction
        for n, line in enumerate(read_lines(path), 1):
            m = ABS_PATH_RE.search(line)
            if m:
                rep.add("WARN", "portability", "absolute home-directory path '%s' only exists on the author's machine" % m.group(1), "%s:%d" % (rel, n))


def iter_files(skill_dir, exts=None):
    for root, dirs, files in os.walk(skill_dir):
        dirs[:] = sorted(d for d in dirs if not d.startswith(".") and d not in ("node_modules", "__pycache__"))
        for f in sorted(files):
            if exts is None or os.path.splitext(f)[1].lower() in exts:
                p = os.path.join(root, f)
                yield p, os.path.relpath(p, skill_dir)


def read_lines(path):
    try:
        return read(path).splitlines()
    except (UnicodeDecodeError, OSError):
        return []


def check_structure(rep, skill_dir, text):
    n = text.count("\n") + 1
    rep.facts["skill_md_lines"] = n
    if n > MAX_LINES:
        rep.add("WARN", "structure", "SKILL.md is %d lines; past %d, split material into reference files" % (n, MAX_LINES), "SKILL.md")
    headings = [h.lower() for h in re.findall(r"^#{2,3}\s+(.+)$", FENCE_RE.sub("", text), re.M)]
    def has(*words):
        return any(any(w in h for w in words) for h in headings)
    if not has("quality bar", "quality", "definition of done", "acceptance"):
        rep.add("WARN", "structure", "no quality-bar section; nothing tells the agent what a passing output looks like", "SKILL.md")
    if not has("anti-pattern", "antipattern", "avoid", "pitfall"):
        rep.add("WARN", "structure", "no anti-patterns section; the known failure modes are left for the agent to rediscover", "SKILL.md")
    if not has("when not", "not to use", "don't use", "do not use"):
        rep.add("WARN", "structure", "no when-not-to-use section; nothing draws the boundary against sibling skills", "SKILL.md")
    if not re.search(r"non-interactive|headless|BLOCKED", text, re.I):
        rep.add("INFO", "structure", "no non-interactive rule; in a subagent or CI run the skill cannot ask its questions", "SKILL.md")
    material = []
    if os.path.isfile(os.path.join(skill_dir, "reference.md")):
        material.append("reference.md")
    for d in MATERIAL_DIRS:
        dp = os.path.join(skill_dir, d)
        if os.path.isdir(dp):
            material += [os.path.join(d, f) for f in sorted(os.listdir(dp)) if f.endswith(".md")]
    for rel in material:
        if rel not in text and os.path.basename(rel) not in text:
            rep.add("WARN", "structure", "%s is never linked from SKILL.md; no agent will read it" % rel, rel)
        else:
            ln = len(read_lines(os.path.join(skill_dir, rel)))
            if ln > 1000:
                rep.add("INFO", "structure", "%s is %d lines; add a table of contents so the agent can jump" % (rel, ln), rel)
    sdir = os.path.join(skill_dir, "scripts")
    if os.path.isdir(sdir):
        for f in sorted(os.listdir(sdir)):
            if os.path.splitext(f)[1].lower() in SCRIPT_EXT and f not in text:
                rep.add("WARN", "structure", "scripts/%s is never mentioned in SKILL.md; the agent will not know to run it" % f, "scripts/" + f)


def check_evals(rep, skill_dir, name):
    ev = os.path.join(skill_dir, "evals", "evals.json")
    qs = os.path.join(skill_dir, "evals", "eval_queries.json")
    if not os.path.isfile(ev):
        rep.add("WARN", "evals", "no evals/evals.json; there is no acceptance prompt to test the skill against", "evals/")
    else:
        try:
            data = json.loads(read(ev))
        except ValueError as e:
            rep.add("ERROR", "evals", "evals.json is not valid JSON: %s" % e, "evals/evals.json")
            data = None
        if data is not None:
            items = data.get("evals") if isinstance(data, dict) else None
            if not isinstance(items, list) or not items:
                rep.add("ERROR", "evals", "evals.json needs {\"skill_name\", \"evals\": [...]} with at least one eval", "evals/evals.json")
            else:
                if data.get("skill_name") != name:
                    rep.add("WARN", "evals", "evals.json skill_name is '%s', not '%s'" % (data.get("skill_name"), name), "evals/evals.json")
                n_assert = 0
                for i, e in enumerate(items, 1):
                    if not isinstance(e, dict) or not e.get("prompt"):
                        rep.add("ERROR", "evals", "eval #%d has no prompt" % i, "evals/evals.json")
                        continue
                    if not isinstance(e.get("assertions"), list) or not e["assertions"]:
                        rep.add("ERROR", "evals", "eval #%d has no assertions; nothing says what a passing output looks like" % i, "evals/evals.json")
                        continue
                    n_assert += len(e["assertions"])
                    if len(e["prompt"]) < 60:
                        rep.add("INFO", "evals", "eval #%d prompt is %d characters; a realistic prompt carries concrete details" % (i, len(e["prompt"])), "evals/evals.json")
                rep.facts["evals"] = len(items)
                rep.facts["assertions"] = n_assert
                if n_assert and n_assert < 3:
                    rep.add("WARN", "evals", "only %d assertion(s); restate the quality bar as checkable claims" % n_assert, "evals/evals.json")
    if not os.path.isfile(qs):
        rep.add("WARN", "evals", "no evals/eval_queries.json; nothing tests whether the description routes correctly", "evals/")
        return
    try:
        q = json.loads(read(qs))
    except ValueError as e:
        rep.add("ERROR", "evals", "eval_queries.json is not valid JSON: %s" % e, "evals/eval_queries.json")
        return
    if not isinstance(q, list) or any(not isinstance(r, dict) or not r.get("query") or not isinstance(r.get("should_trigger"), bool) for r in q):
        rep.add("ERROR", "evals", "eval_queries.json must be a list of {\"query\": str, \"should_trigger\": true|false}", "evals/eval_queries.json")
        return
    pos = sum(1 for r in q if r["should_trigger"])
    neg = len(q) - pos
    rep.facts["trigger_queries"] = pos
    rep.facts["near_miss_queries"] = neg
    if pos < 4:
        rep.add("WARN", "evals", "%d should-trigger queries; write at least 4 phrasings a real user would type" % pos, "evals/eval_queries.json")
    if neg < 3:
        rep.add("WARN", "evals", "%d should-not-trigger queries; write at least 3 near-misses that belong to a named sibling" % neg, "evals/eval_queries.json")


def check_safety(rep, skill_dir):
    for path, rel in iter_files(skill_dir):
        ext = os.path.splitext(path)[1].lower()
        if ext == ".md":
            rules = PROSE_RULES
        elif ext in SCRIPT_EXT:
            rules = SCRIPT_RULES
        else:
            continue
        for n, line in enumerate(read_lines(path), 1):
            if len(line) > 400:
                continue
            for rid, level, owasp, why, rx in rules:
                if rx.search(line):
                    rep.add(level, "safety", "%s: %s [%s]" % (rid, why, owasp), "%s:%d" % (rel, n))


def find_skills(root):
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d != "node_modules"]
        if "SKILL.md" in files:
            yield dirpath
            dirs[:] = []


def check_siblings(rep, skill_dir, name, desc, root):
    mine = content_words(desc)
    scores = []
    me = os.path.realpath(skill_dir)
    for d in find_skills(root):
        if os.path.realpath(d) == me:
            continue
        try:
            fm, _, _ = split_frontmatter(read(os.path.join(d, "SKILL.md")))
        except (OSError, UnicodeDecodeError):
            continue
        meta = parse_frontmatter(fm or "")
        other = meta.get("name") or os.path.basename(d)
        if other == name:
            rep.add("ERROR", "siblings", "another skill is also named '%s'; only one will load" % name, os.path.relpath(d, root))
        theirs = content_words(meta.get("description", ""))
        if mine and theirs:
            j = len(mine & theirs) / float(len(mine | theirs))
            scores.append((j, other, sorted(mine & theirs)))
    scores.sort(reverse=True)
    rep.facts["siblings_compared"] = len(scores)
    rep.facts["closest_siblings"] = [{"skill": s, "overlap": round(j, 2)} for j, s, _ in scores[:3]]
    for j, other, shared in scores[:3]:
        if j >= OVERLAP_WARN:
            rep.add("WARN", "siblings", "description overlaps %d%% with '%s' (shared: %s); add a when-not line and a near-miss query naming it"
                    % (round(j * 100), other, ", ".join(shared[:8])), "SKILL.md")


def render(rep, name):
    out = []
    e, w, i = rep.count("ERROR"), rep.count("WARN"), rep.count("INFO")
    out.append("lint_skill: %s  (%s)" % (name, rep.skill_dir))
    facts = rep.facts
    bits = []
    for k in ("skill_md_lines", "description_chars", "evals", "assertions", "trigger_queries", "near_miss_queries", "siblings_compared"):
        if k in facts:
            bits.append("%s=%s" % (k, facts[k]))
    out.append("  " + "  ".join(bits))
    if facts.get("closest_siblings"):
        out.append("  closest: " + ", ".join("%s %.2f" % (c["skill"], c["overlap"]) for c in facts["closest_siblings"]))
    order = {"ERROR": 0, "WARN": 1, "INFO": 2}
    for f in sorted(rep.findings, key=lambda x: (order[x["level"]], x["area"])):
        out.append("  %-5s %-12s %s%s" % (f["level"], f["area"], f["message"], ("  (" + f["where"] + ")") if f["where"] else ""))
    if not rep.findings:
        out.append("  no findings")
    out.append("result: %d error(s), %d warning(s), %d info -> %s" % (
        e, w, i, "mechanical checks FAIL" if e else ("mechanical checks pass with warnings" if w else "mechanical checks pass")))
    return "\n".join(out) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="Lint the mechanical parts of an Agent Skill folder.")
    ap.add_argument("skill_dir", help="folder that contains SKILL.md")
    ap.add_argument("--siblings", metavar="DIR", help="folder to search for other skills (name clash and description overlap)")
    ap.add_argument("--json", action="store_true", help="print JSON instead of text")
    ap.add_argument("-o", "--output", metavar="PATH", help="also write the report to PATH")
    args = ap.parse_args(argv)

    skill_dir = os.path.abspath(args.skill_dir)
    if not os.path.isdir(skill_dir):
        die("'%s' is not a directory" % args.skill_dir)
    skill_md = os.path.join(skill_dir, "SKILL.md")
    if not os.path.isfile(skill_md):
        die("'%s' has no SKILL.md; point at the skill folder itself, not its parent" % args.skill_dir)
    if args.siblings and not os.path.isdir(args.siblings):
        die("--siblings '%s' is not a directory" % args.siblings)
    try:
        text = read(skill_md)
    except UnicodeDecodeError:
        die("SKILL.md is not UTF-8 text")

    folder = os.path.basename(skill_dir.rstrip(os.sep))
    rep = Report(args.skill_dir)
    meta, _ = check_frontmatter(rep, folder, text)
    name = meta.get("name") or folder
    check_paths(rep, skill_dir, text)
    check_portability(rep, skill_dir, text)
    check_structure(rep, skill_dir, text)
    check_evals(rep, skill_dir, folder)
    check_safety(rep, skill_dir)
    if args.siblings:
        check_siblings(rep, skill_dir, name, meta.get("description", ""), os.path.abspath(args.siblings))

    if args.json:
        result = json.dumps({"skill": name, "dir": skill_dir, "facts": rep.facts,
                             "errors": rep.count("ERROR"), "warnings": rep.count("WARN"),
                             "findings": rep.findings}, indent=2) + "\n"
    else:
        result = render(rep, name)
    sys.stdout.write(result)
    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as fh:
                fh.write(result)
        except OSError as e:
            die("cannot write %s: %s" % (args.output, e))
    return 1 if rep.count("ERROR") else 0


if __name__ == "__main__":
    sys.exit(main())

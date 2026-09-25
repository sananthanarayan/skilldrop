#!/usr/bin/env python3
"""Claude Code plugin-marketplace generator for skilldrop. No deps, no network.
Run from the repo root:

    python3 build_marketplace.py            # write .claude-plugin/{marketplace,plugin}.json
    python3 build_marketplace.py --check    # exit 1 if either committed file is stale
    python3 build_marketplace.py --dist DIR # render the per-pack plugin tree for the branch

One marketplace, seven plugins:

    /plugin marketplace add sananthanarayan/skilldrop
    /plugin install skilldrop@skilldrop            # the whole catalogue
    /plugin install solution-architect@skilldrop   # one role pack

The whole-catalogue plugin's source is the repo root (`"."`): the flat `skills/` and
`agents/` trees are its content, discovered natively on install. Nothing moves and
nothing is projected — the copy-install golden rule in Claude's own plugin format.

A per-pack plugin cannot work that way. A plugin's skills come from a `skills/` folder
inside the plugin, so six role packs need six directories each holding a subset —
physical packs, which RFC-0001 rejected for the source tree. The resolution (RFC-0027)
is `git-subdir`: the plugin entries on main point at `packs/<name>/` on the generated
`plugins` branch, so discovery stays one command against main while the duplicated
trees live only in build output. `skills/<name>` on main is still the only source.

Every field is single-sourced from package.json (name/version/description/author/links)
and packs.json (membership), so a release version bump flows here with no second edit.
validate.py imports `stale()` below and fails the lint if a committed file drifts.
"""
import argparse
import json
import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(ROOT, ".claude-plugin")
SKILLS = os.path.join(ROOT, "skills")
AGENTS = os.path.join(ROOT, "agents")
LOOPS = os.path.join(ROOT, "loops")  # RFC-0028


def _n(count, word):
    """'1 loop', '2 loops' — the description is user-facing copy, not a debug line."""
    return f"{count} {word}" + ("" if count == 1 else "s")

# The catalogue is exposed as a single plugin at the repo root. Both names are
# public and kebab-case; the install command is `skilldrop@skilldrop`.
MARKETPLACE_NAME = "skilldrop"
PLUGIN_NAME = "skilldrop"

# Branch carrying the generated per-pack plugin directories (RFC-0027). Force-pushed by
# .github/workflows/plugins.yml; its history is disposable by design.
DIST_BRANCH = "plugins"

# Same pattern validate.py uses to resolve `x` subagent delegations, so a pack ships the
# reviewer agents its own skills actually hand off to — and no others.
SUBAGENT_REF = re.compile(r"`([a-z0-9][a-z0-9-]*)`\s+subagent")


def _pkg():
    return json.load(open(os.path.join(ROOT, "package.json"), encoding="utf-8"))


def _repo_url(pkg):
    # "git+https://github.com/sananthanarayan/skilldrop.git" -> browsable https URL
    url = pkg.get("repository", {}).get("url", "")
    return url.removeprefix("git+").removesuffix(".git")


def _packs():
    return json.load(open(os.path.join(ROOT, "packs.json"), encoding="utf-8"))["packs"]


def _pack_agents(skill_names):
    """The reviewer subagents this pack's own skills delegate to. A pack that ships
    `pre-merge-review` without `code-quality` would hand the user a dangling delegation."""
    wanted = set()
    for name in skill_names:
        sp = os.path.join(SKILLS, name, "SKILL.md")
        if os.path.exists(sp):
            wanted |= set(SUBAGENT_REF.findall(open(sp, encoding="utf-8").read()))
    return sorted(a for a in wanted if os.path.exists(os.path.join(AGENTS, a + ".md")))


def _pack_plugin_entry(name, pack, version, author, repo):
    """A marketplace entry pointing into the generated branch. `git-subdir` is what lets
    discovery stay on main while the duplicated skill tree lives only in build output."""
    return {
        "name": name,
        "source": {
            "source": "git-subdir",
            "url": repo + ".git",
            "path": f"packs/{name}",
            "ref": DIST_BRANCH,
        },
        "description": f"{pack['description']} ({len(pack['skills'])} skills)",
        "version": version,
        "author": author,
    }


def _render():
    """Return {relative_path: json_text} for every generated file."""
    pkg = _pkg()
    author = pkg["author"]  # {name, url}; added to package.json for exactly this
    version = pkg["version"]
    description = pkg["description"]
    repo = _repo_url(pkg)

    plugin = {
        "name": PLUGIN_NAME,
        "version": version,
        "description": description,
        "author": author,
        "homepage": pkg.get("homepage", repo),
        "repository": repo,
        "license": pkg.get("license", "MIT"),
    }
    packs = _packs()
    marketplace = {
        "name": MARKETPLACE_NAME,
        "owner": {"name": author["name"], "url": author["url"]},
        "plugins": [
            {
                "name": PLUGIN_NAME,
                "source": ".",
                "description": description,
                "version": version,
                "author": author,
            }
        ] + [
            _pack_plugin_entry(n, p, version, author, repo) for n, p in packs.items()
        ],
    }
    dump = lambda obj: json.dumps(obj, indent=2, ensure_ascii=False) + "\n"
    return {
        os.path.join(".claude-plugin", "plugin.json"): dump(plugin),
        os.path.join(".claude-plugin", "marketplace.json"): dump(marketplace),
    }


def stale():
    """Relative paths whose committed content differs from a fresh render (or is
    missing). Imported by validate.py so `python3 validate.py` guards drift in CI."""
    out = []
    for rel, text in _render().items():
        path = os.path.join(ROOT, rel)
        if not os.path.exists(path) or open(path, encoding="utf-8").read() != text:
            out.append(rel)
    return out


def _write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def write():
    os.makedirs(OUT_DIR, exist_ok=True)
    for rel, text in _render().items():
        with open(os.path.join(ROOT, rel), "w", encoding="utf-8") as fh:
            fh.write(text)
        print("wrote", rel)


def render_dist(out):
    """Write the per-pack plugin tree the `plugins` branch carries:

        packs/<pack>/.claude-plugin/plugin.json
        packs/<pack>/skills/<skill>/…      (copied verbatim from skills/<skill>)
        packs/<pack>/skills/<loop>/SKILL.md (a loop; LOOP.md already has SKILL.md's shape)
        packs/<pack>/agents/<agent>.md     (only those the pack's skills delegate to)

    Every file here is derived. The branch is force-pushed, so nothing is ever edited
    in place and a stale directory from a deleted pack cannot survive a rebuild."""
    pkg = _pkg()
    author, version, repo = pkg["author"], pkg["version"], _repo_url(pkg)
    packs = _packs()

    if os.path.exists(out):
        shutil.rmtree(out)
    os.makedirs(out)

    missing = sorted(sk for p in packs.values() for sk in p["skills"]
                     if not os.path.isdir(os.path.join(SKILLS, sk)))
    if missing:
        # A plugin advertising a skill it does not carry is worse than no plugin.
        print("build_marketplace.py: refusing to render — packs.json names skills that do "
              "not exist: " + ", ".join(missing), file=sys.stderr)
        sys.exit(1)
    missing_loops = sorted(lp for p in packs.values() for lp in p.get("loops", [])
                           if not os.path.isfile(os.path.join(LOOPS, lp, "loop.json")))
    if missing_loops:
        print("build_marketplace.py: refusing to render — packs.json names loops that do "
              "not exist: " + ", ".join(missing_loops), file=sys.stderr)
        sys.exit(1)

    for name, pack in packs.items():
        pdir = os.path.join(out, "packs", name)
        os.makedirs(os.path.join(pdir, ".claude-plugin"))
        _write(os.path.join(pdir, ".claude-plugin", "plugin.json"), json.dumps({
            "name": name,
            "version": version,
            "description": f"{pack['description']} ({len(pack['skills'])} skills"
                           + (f", {_n(len(pack.get('loops', [])), 'loop')})" if pack.get("loops") else ")"),
            "author": author,
            "homepage": pkg.get("homepage", repo),
            "repository": repo,
            "license": pkg.get("license", "MIT"),
        }, indent=2, ensure_ascii=False) + "\n")

        for sk in sorted(pack["skills"]):
            shutil.copytree(os.path.join(SKILLS, sk), os.path.join(pdir, "skills", sk),
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

        # RFC-0028: a loop projects into the plugin's skills/ tree, because Claude Code
        # discovers skills/<name>/SKILL.md and has no loop primitive of its own. LOOP.md's
        # frontmatter is already SKILL.md's shape, so this is a rename, not a transform.
        for lp in sorted(pack.get("loops", [])):
            ldest = os.path.join(pdir, "skills", lp)
            os.makedirs(ldest, exist_ok=True)
            shutil.copyfile(os.path.join(LOOPS, lp, "LOOP.md"), os.path.join(ldest, "SKILL.md"))
            shutil.copyfile(os.path.join(LOOPS, lp, "loop.json"), os.path.join(ldest, "loop.json"))

        agents = _pack_agents(pack["skills"])
        for a in agents:
            os.makedirs(os.path.join(pdir, "agents"), exist_ok=True)
            shutil.copyfile(os.path.join(AGENTS, a + ".md"),
                            os.path.join(pdir, "agents", a + ".md"))
        print(f"  packs/{name}: {len(pack['skills'])} skills"
              + (f", {_n(len(pack.get('loops', [])), 'loop')}" if pack.get("loops") else "")
              + (f", {len(agents)} agents" if agents else ""))

    _write(os.path.join(out, "README.md"),
           "# skilldrop — generated plugin branch\n\n"
           f"Generated by `build_marketplace.py --dist` from [`main`]({repo}) at v{version}. "
           "**Do not edit or open pull requests against this branch** — it is force-pushed on "
           "every push to main and any commit here is discarded.\n\n"
           "Each `packs/<name>/` is a Claude Code plugin: a subset of the catalogue with its own "
           "`.claude-plugin/plugin.json`, the pack's `skills/`, and the reviewer `agents/` those "
           "skills delegate to. The marketplace that points here lives on main, so install with:\n\n"
           "```\n/plugin marketplace add sananthanarayan/skilldrop\n"
           "/plugin install <pack-name>@skilldrop\n```\n\n"
           f"Source of truth is the flat `skills/` tree on main. Rationale: RFC-0027.\n")
    print(f"\n{len(packs)} pack plugins rendered into {out}")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="exit 1 if any file is stale")
    ap.add_argument("--dist", metavar="DIR",
                    help=f"render the per-pack plugin tree for the `{DIST_BRANCH}` branch")
    args = ap.parse_args()
    if args.dist:
        render_dist(os.path.abspath(args.dist))
        return
    if args.check:
        drifted = stale()
        if drifted:
            print("stale (run `python3 build_marketplace.py`):")
            for rel in drifted:
                print("  ", rel)
            sys.exit(1)
        print("OK: .claude-plugin/ is up to date")
        return
    write()


if __name__ == "__main__":
    main()

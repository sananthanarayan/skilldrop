#!/usr/bin/env python3
"""Claude Code plugin-marketplace generator for skilldrop. No deps, no network.
Run from the repo root:

    python3 build_marketplace.py           # write .claude-plugin/{marketplace,plugin}.json
    python3 build_marketplace.py --check    # exit 1 if either file is stale

This makes skilldrop installable as a Claude Code plugin marketplace:

    /plugin marketplace add sananthanarayan/skilldrop
    /plugin install skilldrop@skilldrop

The catalogue ships as ONE plugin whose source is the repo root (`"."`): the flat
`skills/` and `agents/` trees are the plugin's content, discovered natively when the
plugin is installed. Nothing moves and nothing is projected — the copy-install golden
rule expressed in Claude's own plugin format. Per-pack plugin granularity (one plugin
per role bundle in packs.json) would need generated plugin directories on a dist
branch; that is a deliberately deferred step — see docs/rfcs/0014-agentbundle-interop.md.

Every field is single-sourced from package.json (name/version/description/author/
links), so a release version bump flows here with no second edit. validate.py imports
`stale()` below and fails the lint if a committed file drifts from this generator.
"""
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(ROOT, ".claude-plugin")

# The catalogue is exposed as a single plugin at the repo root. Both names are
# public and kebab-case; the install command is `skilldrop@skilldrop`.
MARKETPLACE_NAME = "skilldrop"
PLUGIN_NAME = "skilldrop"


def _pkg():
    return json.load(open(os.path.join(ROOT, "package.json"), encoding="utf-8"))


def _repo_url(pkg):
    # "git+https://github.com/sananthanarayan/skilldrop.git" -> browsable https URL
    url = pkg.get("repository", {}).get("url", "")
    return url.removeprefix("git+").removesuffix(".git")


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


def write():
    os.makedirs(OUT_DIR, exist_ok=True)
    for rel, text in _render().items():
        with open(os.path.join(ROOT, rel), "w", encoding="utf-8") as fh:
            fh.write(text)
        print("wrote", rel)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="exit 1 if any file is stale")
    args = ap.parse_args()
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

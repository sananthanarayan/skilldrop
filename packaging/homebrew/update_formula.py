#!/usr/bin/env python3
"""Point the Homebrew formula at a published npm version: rewrite its url and sha256.

  python3 packaging/homebrew/update_formula.py            # the version in package.json
  python3 packaging/homebrew/update_formula.py 0.13.8

It downloads the tarball from the npm registry and hashes it, so run it after the release is
approved and live on npm (`npm view skilldrop-cli version`). Then copy skilldrop.rb into the
tap repository's Formula/ folder; see README.md beside this script.
"""
import hashlib
import json
import os
import re
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FORMULA = os.path.join(HERE, "skilldrop.rb")


def main():
    version = sys.argv[1] if len(sys.argv) > 1 else json.load(open(os.path.join(ROOT, "package.json")))["version"]
    with urllib.request.urlopen(f"https://registry.npmjs.org/skilldrop-cli/{version}", timeout=30) as r:
        dist = json.load(r)["dist"]
    with urllib.request.urlopen(dist["tarball"], timeout=60) as r:
        digest = hashlib.sha256(r.read()).hexdigest()
    rb = open(FORMULA).read()
    rb = re.sub(r'url "[^"]+"', f'url "{dist["tarball"]}"', rb, count=1)
    rb = re.sub(r'sha256 "[0-9a-f]*"', f'sha256 "{digest}"', rb, count=1)
    open(FORMULA, "w").write(rb)
    print(f"skilldrop.rb -> {version}\n  {dist['tarball']}\n  sha256 {digest}")


if __name__ == "__main__":
    main()

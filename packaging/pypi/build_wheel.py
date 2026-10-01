#!/usr/bin/env python3
"""Build a PyPI wheel of skilldrop-cli, so `pipx install skilldrop-cli` works.

The CLI is Node, so the wheel carries the same files the npm package ships (package.json's
`files`) plus a small Python launcher that runs them with the `node` on your PATH. It needs
Node 16.7+ at run time, the same as npx, and says so plainly when node is missing.

  python3 packaging/pypi/build_wheel.py          # wheel + sdist in dist/
  python3 -m twine upload dist/*                 # maintainer only, with a PyPI token

Needs the `build` package (python3 -m pip install build). Stdlib otherwise.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))

LAUNCHER = '''"""Run the skilldrop CLI (Node) that ships inside this package."""
import os
import shutil
import subprocess
import sys

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def main():
    node = shutil.which("node")
    if not node:
        sys.exit("skilldrop needs Node.js 16.7 or newer on your PATH: https://nodejs.org/ "
                 "(or install it with: brew install node)")
    cli = os.path.join(DATA, "bin", "skilldrop.js")
    sys.exit(subprocess.call([node, cli, *sys.argv[1:]]))
'''


def main():
    pkg = json.load(open(os.path.join(ROOT, "package.json")))
    out = os.path.join(ROOT, "dist")
    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, "skilldrop_cli")
        data = os.path.join(src, "data")
        os.makedirs(data)
        for entry in pkg["files"] + ["package.json", "LICENSE"]:
            s = os.path.join(ROOT, entry.rstrip("/"))
            d = os.path.join(data, entry.rstrip("/"))
            if os.path.isdir(s):
                shutil.copytree(s, d, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"))
            else:
                shutil.copy2(s, d)
        open(os.path.join(src, "__init__.py"), "w").write(LAUNCHER)
        open(os.path.join(src, "__main__.py"), "w").write("from . import main\n\nmain()\n")
        shutil.copy2(os.path.join(ROOT, "README.md"), tmp)
        shutil.copy2(os.path.join(ROOT, "LICENSE"), tmp)
        open(os.path.join(tmp, "pyproject.toml"), "w").write(f'''[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "skilldrop-cli"
version = "{pkg['version']}"
description = "{pkg['description'].replace('"', "'")}"
readme = "README.md"
license = {{ text = "MIT" }}
requires-python = ">=3.8"
keywords = ["ai", "agent", "skills", "claude-code", "cursor", "kiro", "codex"]
classifiers = ["Environment :: Console", "License :: OSI Approved :: MIT License", "Programming Language :: JavaScript"]

[project.urls]
Homepage = "https://sananthanarayan.github.io/skilldrop/"
Source = "https://github.com/sananthanarayan/skilldrop"

[project.scripts]
skilldrop = "skilldrop_cli:main"

[tool.setuptools]
packages = ["skilldrop_cli"]
include-package-data = true

[tool.setuptools.package-data]
skilldrop_cli = ["data/**/*"]
''')
        # cwd=tmp: run from the repo root, the site's build/ folder would shadow the build package
        subprocess.run([sys.executable, "-m", "build", "--outdir", out, tmp], check=True, cwd=tmp)
    print(f"built skilldrop-cli {pkg['version']} into {os.path.relpath(out, ROOT)}/")


if __name__ == "__main__":
    main()

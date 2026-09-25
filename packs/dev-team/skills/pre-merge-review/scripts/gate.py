#!/usr/bin/env python3
"""Mechanical merge gate — run a project's verify commands and exit non-zero if any fail.

The deterministic half of `pre-merge-review`: the pass/fail verdict comes from *running real
commands*, not from a judgment call, so an agent can't talk its way past a red gate. The commands
are the operator's own (auto-detected, or supplied) — this is a local dev tool, not a sandbox.

  python3 gate.py                      # auto-detect lint / typecheck / test for the project
  python3 gate.py --cmd "npm test" --cmd "npm run lint"   # explicit commands (repeatable)
  python3 gate.py --config gate.json   # {"commands": ["pytest -q", "ruff check ."]}
  python3 gate.py --list               # print what it would run, don't run
  python3 gate.py --root path/to/repo  # run against another project root

Precedence: --cmd (explicit) > --config > auto-detect. Runs each command in order, streams its
output, prints a PASS/FAIL line per command and an overall verdict. Exit 0 iff every command
passed; 1 if any failed; 2 if there was nothing to run. Stdlib only; no network.
"""
import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import sys

HOOK_MARKER = "skilldrop-gate"


def detect(root):
    """Best-effort verify commands for common stacks. Modest on purpose — an operator with a
    non-standard setup passes --cmd/--config; auto-detect covers the usual cases."""
    cmds = []
    has = lambda f: os.path.exists(os.path.join(root, f))

    if any(has(f) for f in ("pyproject.toml", "setup.py", "pytest.ini", "tox.ini")):
        if shutil.which("ruff"):
            cmds.append("ruff check .")
        if shutil.which("mypy") and has("mypy.ini") or (shutil.which("mypy") and has("pyproject.toml")):
            cmds.append("mypy .")
        if shutil.which("pytest"):
            cmds.append("pytest -q")

    if has("package.json"):
        try:
            scripts = json.load(open(os.path.join(root, "package.json"))).get("scripts", {})
        except (OSError, json.JSONDecodeError):
            scripts = {}
        if "lint" in scripts:
            cmds.append("npm run lint")
        if "typecheck" in scripts:
            cmds.append("npm run typecheck")
        if "test" in scripts:
            cmds.append("npm test")

    if has("go.mod"):
        cmds += ["go vet ./...", "go test ./..."]

    if not cmds and has("Makefile"):
        mk = "\n" + open(os.path.join(root, "Makefile"), encoding="utf-8", errors="replace").read()
        cmds += [f"make {t}" for t in ("lint", "typecheck", "test") if f"\n{t}:" in mk]

    return cmds


def load_config(path):
    data = json.load(open(path, encoding="utf-8"))
    cmds = data.get("commands") if isinstance(data, dict) else data
    if not isinstance(cmds, list) or not all(isinstance(c, str) for c in cmds):
        raise SystemExit("gate: --config must hold a list of command strings (or {\"commands\": [...]})")
    return cmds


# --- opt-in harness: a blocking git pre-commit hook (Layer 1) ---------------------------
# The portable enforcement point — git runs it regardless of which agent/tool wrote the code.
# Bypassable with `git commit --no-verify`; CI required-checks are the un-bypassable backstop.

def _hooks_dir(root):
    r = subprocess.run(["git", "rev-parse", "--git-path", "hooks"], cwd=root, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit("gate: not a git repository — run --install-hook from inside your repo")
    hd = r.stdout.strip()
    return hd if os.path.isabs(hd) else os.path.join(root, hd)


def _hook_block(cmd, config):
    inv = f"python3 {shlex.quote(os.path.abspath(__file__))}"
    for c in cmd:
        inv += f" --cmd {shlex.quote(c)}"
    if config:
        inv += f" --config {shlex.quote(os.path.abspath(config))}"
    return (
        f"# >>> {HOOK_MARKER} >>>  pre-merge-review gate — run `gate.py --uninstall-hook` to remove\n"
        f"{inv} || {{ echo 'skilldrop-gate: commit blocked (gate RED). Fix it, or override once with "
        f"--no-verify — CI required-checks still gate the merge.' >&2; exit 1; }}\n"
        f"# <<< {HOOK_MARKER} <<<\n"
    )


def install_hook(root, cmd, config):
    hooks = _hooks_dir(root)
    os.makedirs(hooks, exist_ok=True)
    path = os.path.join(hooks, "pre-commit")
    body = open(path, encoding="utf-8").read() if os.path.exists(path) else ""
    if HOOK_MARKER in body:
        print(f"gate: hook already installed at {path} — --uninstall-hook then --install-hook to change its commands")
        return 0
    if not body.startswith("#!"):
        body = "#!/bin/sh\n" + body
    if body and not body.endswith("\n"):
        body += "\n"
    body += "\n" + _hook_block(cmd, config)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(body)
    os.chmod(path, 0o755)
    print(f"gate: installed a blocking pre-commit hook -> {path}")
    print("      a RED gate now blocks `git commit` (any tool). Bypass once with --no-verify; "
          "wire CI required-checks for the un-bypassable backstop.")
    return 0


def uninstall_hook(root):
    path = os.path.join(_hooks_dir(root), "pre-commit")
    if not os.path.exists(path):
        print("gate: no pre-commit hook to remove")
        return 0
    body = open(path, encoding="utf-8").read()
    new = re.sub(rf"\n?# >>> {HOOK_MARKER} >>>.*?# <<< {HOOK_MARKER} <<<\n?", "\n", body, flags=re.S)
    if new == body:
        print(f"gate: no {HOOK_MARKER} block in {path} — left untouched")
        return 0
    open(path, "w", encoding="utf-8").write(new)
    print(f"gate: removed the {HOOK_MARKER} block from {path}")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cmd", action="append", default=[], help="a verify command (repeatable)")
    ap.add_argument("--config", help='JSON file: {"commands": [...]}')
    ap.add_argument("--root", default=".", help="project root (default: cwd)")
    ap.add_argument("--list", action="store_true", help="print the commands the gate would run, don't run them")
    ap.add_argument("--install-hook", action="store_true",
                    help="install a blocking git pre-commit hook that runs this gate (with the given --cmd/--config)")
    ap.add_argument("--uninstall-hook", action="store_true", help="remove the skilldrop-gate pre-commit hook block")
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    if args.uninstall_hook:
        return uninstall_hook(root)
    if args.install_hook:
        return install_hook(root, args.cmd, args.config)
    cmds = args.cmd or (load_config(args.config) if args.config else detect(root))
    if not cmds:
        print("gate: no verify commands — pass --cmd/--config, or run inside a project the gate can "
              "detect (Python / Node / Go / Makefile).", file=sys.stderr)
        return 2

    if args.list:
        print("gate would run, in order:")
        for c in cmds:
            print("  -", c)
        return 0

    results = []
    for c in cmds:
        print(f"\n=== gate: {c} ===", flush=True)
        rc = subprocess.run(c, shell=True, cwd=root).returncode  # operator-supplied commands, by design
        results.append((c, rc))
        print(f"--- {'PASS' if rc == 0 else 'FAIL'} ({c}) rc={rc} ---", flush=True)

    print("\n" + "=" * 48)
    for c, rc in results:
        print(f"  {'PASS' if rc == 0 else 'FAIL'}  {c}")
    print("=" * 48)

    failed = [c for c, rc in results if rc != 0]
    if failed:
        print(f"GATE: RED — {len(failed)}/{len(results)} command(s) failed. Change is NOT READY to merge.")
        return 1
    print(f"GATE: GREEN — all {len(results)} command(s) passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

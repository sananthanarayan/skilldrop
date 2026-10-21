"""Shared helpers for the skill script tests (RFC-0060).

Every test runs offline, with the standard library only, on Linux, macOS and Windows:

    python3 -m unittest discover -s tests -t .

Two ways to reach a script:

  load(skill, script)  import it as a module, to test its functions directly. The script's
                       own folder goes on sys.path first, so a sibling import such as
                       figma-diagrams' `_figma_client` resolves the way it does when it runs.
  run(skill, script, *args, stdin=None, cwd=None)
                       run it as a user would, in a fresh interpreter, and return
                       (exit code, stdout, stderr), all text.

workdir() gives a throwaway folder; write(path, text) writes UTF-8 with Unix newlines.
"""
import contextlib
import importlib.util
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import catalog  # noqa: E402  (the repo root must be importable first)


def script_path(skill, script):
    path = os.path.join(catalog.skill_dir(skill), "scripts", script)
    if not os.path.isfile(path):
        raise FileNotFoundError(f"{skill} has no scripts/{script}")
    return path


def load(skill, script):
    """Import scripts/<script> from <skill> as a fresh module (never cached between tests)."""
    path = script_path(skill, script)
    name = f"skilltest_{skill.replace('-', '_')}_{os.path.splitext(script)[0]}"
    here = os.path.dirname(path)
    sys.path.insert(0, here)
    try:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        # Registered before it runs, as a normal import is: @dataclass under
        # `from __future__ import annotations` looks its module up in sys.modules.
        sys.modules[name] = mod
        try:
            spec.loader.exec_module(mod)
        except BaseException:
            del sys.modules[name]
            raise
    finally:
        sys.path.remove(here)
    return mod


def run(skill, script, *args, stdin=None, cwd=None, env=None, timeout=60):
    """Run a script as a command. Output is decoded as UTF-8 whatever the platform's default,
    because the scripts write UTF-8 (validate.py's check_text_encoding)."""
    full_env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
    if env:
        full_env.update(env)
    r = subprocess.run([sys.executable, script_path(skill, script), *map(str, args)],
                       input=stdin, cwd=cwd, env=full_env, capture_output=True,
                       text=True, encoding="utf-8", errors="replace", timeout=timeout)
    return r.returncode, r.stdout, r.stderr


@contextlib.contextmanager
def workdir():
    with tempfile.TemporaryDirectory() as d:
        yield d


def write(path, text):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    return path


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def has_module(name):
    return importlib.util.find_spec(name) is not None

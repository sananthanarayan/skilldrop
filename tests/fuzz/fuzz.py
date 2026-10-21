#!/usr/bin/env python3
"""Fuzz the skill scripts that parse users' files (RFC-0062).

With Atheris installed (Linux CI; .github/tools/requirements-fuzz.txt), the fuzzing is
coverage-guided: the script is instrumented and libFuzzer drives the mutations. Without it,
a small standard-library mutator runs the same targets, so they work on any OS and in the unit
tests (tests/test_fuzz_targets.py).

    python3 tests/fuzz/fuzz.py --list
    python3 tests/fuzz/fuzz.py --target sql --seconds 30       # one target
    python3 tests/fuzz/fuzz.py --all --seconds 30              # every target, each in its own process
    python3 tests/fuzz/fuzz.py --target sql --iterations 500   # the standard-library mutator

A crash prints the input that caused it and saves it to fuzz-crashes/<target>-<sha>.bin, then
exits 1. Reproduce one with: python3 tests/fuzz/fuzz.py --target sql --replay <file>
"""
import argparse
import hashlib
import os
import random
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

try:
    import atheris
except ImportError:  # macOS, Windows, or no Atheris: the standard-library mutator below
    atheris = None

from tests.fuzz.targets import BY_NAME, TARGETS, Crash, runner  # noqa: E402

# Byte strings that often break parsers: structure, encodings, sizes, separators.
TOKENS = [b"{", b"}", b"[", b"]", b'"', b",", b":", b"\n", b"\r\n", b"\x00", b"\xef\xbb\xbf", b"\xff\xfe",
          b"\\", b"null", b"true", b"-1", b"1e309", b"NaN", b"0", b"[]", b"{}", b'""', b"\t", b";", b"|",
          b"#", b"--", b"/*", b"'", b"\xe9", b"\xc3\x28", "‮".encode(), b"9" * 40]


def mutate(data, rng):
    b = bytearray(data)
    for _ in range(rng.randint(1, 4)):
        op = rng.randrange(6)
        pos = rng.randint(0, len(b))
        if op == 0 and b:
            b[min(pos, len(b) - 1)] = rng.randrange(256)
        elif op == 1:
            b[pos:pos] = rng.choice(TOKENS)
        elif op == 2 and b:
            del b[pos:pos + rng.randint(1, 16)]
        elif op == 3 and b:
            start = rng.randint(0, len(b) - 1)
            b[pos:pos] = b[start:start + rng.randint(1, 32)]
        elif op == 4:
            b = b[:pos]
        else:
            b[pos:pos] = rng.choice(TOKENS) * rng.randint(2, 8)
    return bytes(b)


def save(name, data):
    os.makedirs("fuzz-crashes", exist_ok=True)
    path = os.path.join("fuzz-crashes", "%s-%s.bin" % (name, hashlib.sha256(data).hexdigest()[:12]))
    with open(path, "wb") as fh:
        fh.write(data)
    return path


def stdlib_fuzz(name, iterations, seed=1):
    """Mutate the seeds; return (input, error) for the first crash, or None."""
    one = runner(name)
    seeds = BY_NAME[name][6]
    rng = random.Random("%s-%d" % (name, seed))
    for s in seeds:
        try:
            one(s)
        except Crash as e:
            return s, e
    for _ in range(iterations):
        data = mutate(rng.choice(seeds), rng)
        try:
            one(data)
        except Crash as e:
            return data, e
    return None


def atheris_fuzz(name, seconds):
    one = runner(name)
    # The script is loaded from its file path (tests/support.py), which import hooks may not see,
    # so instrument everything that is loaded now for coverage guidance.
    atheris.instrument_all()
    corpus = os.path.join("fuzz-corpus", name)
    os.makedirs(corpus, exist_ok=True)
    for i, s in enumerate(BY_NAME[name][6]):
        with open(os.path.join(corpus, "seed-%d" % i), "wb") as fh:
            fh.write(s)

    def test_one(data):
        try:
            one(data)
        except Crash:
            print("crash input saved to", save(name, data), file=sys.stderr)
            raise

    # An input that takes over 10 seconds or 2 GB counts as a crash too: a small file that hangs a
    # script or fills memory (a looping sector chain, one cell at ZZZ999999) is a finding.
    atheris.Setup([sys.argv[0], "-max_total_time=%d" % seconds, "-timeout=10", "-rss_limit_mb=2048", corpus], test_one)
    atheris.Fuzz()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--target", choices=sorted(BY_NAME))
    g.add_argument("--all", action="store_true")
    g.add_argument("--list", action="store_true")
    ap.add_argument("--seconds", type=int, default=30, help="per target, with Atheris")
    ap.add_argument("--iterations", type=int, default=0, help="use the standard-library mutator for this many inputs")
    ap.add_argument("--replay", metavar="FILE", help="run one saved input through the target")
    a = ap.parse_args(argv)

    if a.list:
        for t in TARGETS:
            print("%-16s %s/%s" % (t[0], t[1], t[2]))
        return 0
    if a.all:
        failed = []
        for t in TARGETS:
            cmd = [sys.executable, os.path.abspath(__file__), "--target", t[0], "--seconds", str(a.seconds)]
            if a.iterations:
                cmd += ["--iterations", str(a.iterations)]
            print("== %s" % t[0], flush=True)
            if subprocess.run(cmd).returncode != 0:
                failed.append(t[0])
        print("\n%d target(s), %d crashed%s" % (len(TARGETS), len(failed), (": " + ", ".join(failed)) if failed else ""))
        return 1 if failed else 0
    if a.replay:
        with open(a.replay, "rb") as fh:
            runner(a.target)(fh.read())
        print("no crash")
        return 0
    if atheris and not a.iterations:
        atheris_fuzz(a.target, a.seconds)
        return 0
    found = stdlib_fuzz(a.target, a.iterations or 2000)
    if found:
        data, err = found
        print("CRASH %s\n  input saved to %s\n  %r" % (err, save(a.target, data), data[:300]), file=sys.stderr)
        return 1
    print("%s: no crash in %d inputs" % (a.target, a.iterations or 2000))
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Find where a leaked key appears in a repository's git history and in log files.

Read-only. Never prints the key: every match is shown masked (first 8 characters,
an ellipsis, the last 4, and the length). Identify the key by a prefix you already
know (--prefix, optionally with --suffix for the last characters) or by piping the
full key on stdin (--key-stdin) so it never lands in shell history.

    python3 find_secret_exposure.py --prefix sk-live-AbCdEf12 --repo . --log ci.txt
    printf '%s' "$LEAKED" | python3 find_secret_exposure.py --key-stdin --repo .

Reports: commits that added or removed it (author and commit time, UTC), whether the
current tree and working copy still hold it, which branches and tags still reach the
adding commits, commits reachable only from the local reflog, and every log line that
holds it with the line's own timestamp. Writes only the -o path when given.
"""
import argparse
import datetime as dt
import os
import re
import subprocess
import sys

TOKEN_CHARS = r"[A-Za-z0-9_\-+/=.]"
STAMP = re.compile(
    r"(\d{4}-\d{2}-\d{2})[T ](\d{2}:\d{2}:\d{2})(?:\.\d+)?(Z|[+-]\d{2}:?\d{2})?"
)
MIN_PREFIX = 10


def mask(token):
    if len(token) <= 12:
        return token[:4] + "…" + " (len %d)" % len(token)
    return "%s…%s (len %d)" % (token[:8], token[-4:], len(token))


class Needle:
    def __init__(self, prefix=None, suffix=None, full=None):
        self.full = full
        self.prefix = full[:12] if full else prefix
        self.suffix = suffix
        self.rx = re.compile(re.escape(self.prefix) + TOKEN_CHARS + "*")
        self.seen = set()

    def tokens(self, text):
        """Masked tokens in text that match the key."""
        out = []
        for m in self.rx.finditer(text):
            tok = m.group(0).rstrip(".=")  # trailing punctuation from prose or logs
            if self.full and self.full not in m.group(0):
                continue
            if self.suffix and not tok.endswith(self.suffix):
                continue
            out.append(mask(self.full if self.full else tok))
        self.seen.update(out)
        return out


def utc(epoch):
    return dt.datetime.fromtimestamp(int(epoch), dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")


def line_stamp(line):
    m = STAMP.search(line)
    if not m:
        return "no timestamp on the line"
    day, clock, tz = m.groups()
    if not tz:
        return "%s %s (no timezone on the line)" % (day, clock)
    tz = "+00:00" if tz == "Z" else (tz if ":" in tz else tz[:3] + ":" + tz[3:])
    try:
        when = dt.datetime.fromisoformat("%sT%s%s" % (day, clock, tz))
    except ValueError:
        return "%s %s%s (unparsed)" % (day, clock, tz)
    return when.astimezone(dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")


def git(repo, *args):
    r = subprocess.run(["git", "-C", repo] + list(args), capture_output=True)
    return r.returncode, r.stdout.decode("utf-8", "replace"), r.stderr.decode("utf-8", "replace")


def scan_repo(repo, needle):
    rc, _, err = git(repo, "rev-parse", "--git-dir")
    if rc != 0:
        return None, "not a git repository: %s (%s)" % (repo, err.strip())
    rc, out, err = git(
        repo, "log", "--all", "--reflog", "--no-color", "--no-ext-diff", "-p",
        "-S" + needle.prefix, "--format=%x00COMMIT %H %at %ct",
    )
    if rc != 0:
        return None, "git log failed: %s" % err.strip()
    commits, cur, path = [], None, None
    for line in out.splitlines():
        if line.startswith("\x00COMMIT "):
            sha, at, ct = line.split()[1:4]
            cur = {"sha": sha, "authored": utc(at), "committed": utc(ct), "added": [], "removed": []}
            commits.append(cur)
        elif cur is None:
            continue
        elif line.startswith("diff --git "):
            path = line.split(" b/", 1)[-1]
        elif line.startswith("+") and not line.startswith("+++"):
            if needle.tokens(line):
                cur["added"].append(path)
        elif line.startswith("-") and not line.startswith("---"):
            if needle.tokens(line):
                cur["removed"].append(path)
    commits = [c for c in commits if c["added"] or c["removed"]]
    for c in commits:
        c["added"], c["removed"] = sorted(set(c["added"])), sorted(set(c["removed"]))
        if c["added"]:
            _, b, _ = git(repo, "branch", "-a", "--contains", c["sha"])
            _, t, _ = git(repo, "tag", "--contains", c["sha"])
            c["refs"] = [x.strip("* ").strip() for x in b.splitlines() if x.strip()]
            c["refs"] += ["tag " + x.strip() for x in t.splitlines() if x.strip()]
    present = {}
    for label, args in (("HEAD", ["grep", "-n", "-I", "-F", "-e", needle.prefix, "HEAD", "--"]),
                        ("working copy", ["grep", "-n", "-I", "-F", "--untracked", "-e", needle.prefix])):
        _, g, _ = git(repo, *args)
        hits = []
        for gl in g.splitlines():
            parts = gl.split(":", 3 if label == "HEAD" else 2)
            loc = ":".join(parts[1:3]) if label == "HEAD" else ":".join(parts[0:2])
            if needle.tokens(gl):
                hits.append(loc)
        present[label] = hits
    return {"commits": commits, "present": present}, None


def scan_log(path, needle):
    hits = []
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        for n, line in enumerate(fh, 1):
            toks = needle.tokens(line)
            if toks:
                hits.append((n, line_stamp(line), toks[0]))
    return hits


def report(args, needle, repo_res, repo_err, logs):
    o = ["# Where the key appears", ""]
    if len(needle.seen) > 1:
        o += ["%d different keys match this prefix: %s. Pass --suffix with the leaked key's last "
              "characters to keep only that one." % (len(needle.seen), ", ".join(sorted(needle.seen))), ""]
    if args.repo:
        o.append("## Git history: %s" % args.repo)
        if repo_err:
            o += ["", "Not scanned: " + repo_err]
        else:
            cs = repo_res["commits"]
            adds = [c for c in cs if c["added"]]
            if not cs:
                o += ["", "No commit adds or removes it (searched every branch, tag, stash and the local reflog)."]
            if adds:
                first = min(adds, key=lambda c: c["authored"])
                o += ["", "First commit that adds it: `%s`, authored %s, committed %s. Commit time is "
                      "when it was committed locally; when it reached a remote is in the host's audit or push log."
                      % (first["sha"][:12], first["authored"], first["committed"])]
            for c in cs:
                o.append("")
                o.append("- `%s` authored %s, committed %s" % (c["sha"][:12], c["authored"], c["committed"]))
                if c["added"]:
                    o.append("  - adds it in: %s" % ", ".join(c["added"]))
                    o.append("  - still reachable from: %s" % (", ".join(c["refs"]) if c["refs"]
                             else "no branch or tag; only the local reflog keeps it"))
                if c["removed"]:
                    o.append("  - removes it from: %s (the earlier commits still hold it)" % ", ".join(c["removed"]))
            for label, hits in repo_res["present"].items():
                o.append("")
                o.append("In %s now: %s" % (label, ", ".join(hits) if hits else "not present"))
        o.append("")
    for path, hits, err in logs:
        o.append("## Log: %s" % path)
        o.append("")
        if err:
            o.append("Not scanned: " + err)
        elif not hits:
            o.append("Not found.")
        else:
            for n, stamp, tok in hits:
                o.append("- line %d, %s, %s" % (n, stamp, tok))
        o.append("")
    o += ["## Not searched", "",
          "Forks, other clones, pull-request refs that were never fetched, CI caches and artifacts, "
          "the hosting provider's own copies, chat and ticket systems. A clean result here does not "
          "mean the key is safe: revoke it regardless.", ""]
    return "\n".join(o)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    who = p.add_mutually_exclusive_group(required=True)
    who.add_argument("--prefix", help="the first characters of the key (at least %d)" % MIN_PREFIX)
    who.add_argument("--key-stdin", action="store_true", help="read the full key from stdin")
    p.add_argument("--suffix", help="the last characters of the key, to tell it apart from keys with the same prefix")
    p.add_argument("--repo", help="path to a git repository to search")
    p.add_argument("--log", action="append", default=[], help="a log file to search (repeatable)")
    p.add_argument("-o", "--out", help="write the report here instead of stdout")
    a = p.parse_args(argv)
    if a.key_stdin:
        full = sys.stdin.read().strip()
        if len(full) < MIN_PREFIX:
            p.error("the key on stdin is shorter than %d characters" % MIN_PREFIX)
        needle = Needle(full=full)
    else:
        if len(a.prefix) < MIN_PREFIX:
            p.error("--prefix needs at least %d characters: a short prefix such as a provider's "
                    "key-type marker matches every key of that type" % MIN_PREFIX)
        needle = Needle(prefix=a.prefix, suffix=a.suffix)
    if not a.repo and not a.log:
        p.error("give --repo, --log, or both")
    repo_res, repo_err = (None, None)
    if a.repo:
        if not os.path.isdir(a.repo):
            repo_err = "no such directory: %s" % a.repo
        else:
            repo_res, repo_err = scan_repo(a.repo, needle)
    logs = []
    for path in a.log:
        if not os.path.isfile(path):
            logs.append((path, [], "no such file"))
            continue
        try:
            logs.append((path, scan_log(path, needle), None))
        except OSError as e:
            logs.append((path, [], str(e)))
    text = report(a, needle, repo_res, repo_err, logs)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as fh:
            fh.write(text)
        print("wrote %s" % a.out)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())

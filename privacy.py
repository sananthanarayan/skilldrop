#!/usr/bin/env python3
"""Keep the maintainers' own identity out of a public repository (RFC-0049).

An agent session knows who is signed in, and a model will write that person's name into an
"Author" field or a contact line without being asked. Git will record whatever email the
machine is configured with. This checks both, using identifiers it reads from this machine at
run time, so the list of what to protect is never itself committed:

  - the signed-in Claude account (~/.claude.json: name, email, organization)
  - git config user.name and user.email, unless the email is a GitHub noreply address
  - the operating-system user name and home directory
  - the organisation name in a work email's domain (example.co.uk -> example)
  - SKILLDROP_PRIVATE_TERMS (comma or newline separated) and .skilldrop-private (git-ignored,
    one term per line): anything else, such as a second email or a client's name

A match is reported by kind ("your account email") and never printed, so a CI log can't leak
what it protects. The maintainer's name is allowed only in the files that publish it on
purpose (ATTRIBUTION below); email, organization and home paths are allowed nowhere.

  python3 privacy.py --staged          # staged changes and the commit identity (pre-commit hook)
  python3 privacy.py --message FILE    # a commit message (commit-msg hook)
  python3 privacy.py --tree            # every tracked text file (validate.py runs this)
  python3 privacy.py --commits A..B    # author and committer emails of a range (CI)

Standard library only. Exit 0 when clean, 1 on a finding, 2 on a usage error.
"""
import argparse
import fnmatch
import functools
import getpass
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
# Files that publish the maintainer's name on purpose. Only "name" terms are allowed here.
ATTRIBUTION = ["package.json", "LICENSE", "LICENSE-*", ".claude-plugin/*.json", "build_site.py"]
NOREPLY = re.compile(r"^(\d+\+)?[A-Za-z0-9-]+(\[bot\])?@users\.noreply\.github\.com$|^noreply@github\.com$", re.I)
SKIP_EXT = (".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf", ".zip", ".woff", ".woff2", ".ttf", ".docx", ".xlsx", ".pptx")


def _git(*args):
    try:
        return subprocess.run(["git"] + list(args), cwd=ROOT, capture_output=True, text=True, timeout=30).stdout
    except (OSError, subprocess.SubprocessError):
        return ""


# Domain endings that aren't an organisation's name: generic and country top-level domains, and
# the second-level parts some countries use (co.uk, com.au).
_SUFFIXES = {"com", "org", "net", "edu", "gov", "mil", "int", "io", "co", "ac", "ltd", "plc", "biz", "info",
             "uk", "us", "au", "nz", "ca", "in", "ie", "de", "fr", "nl", "es", "it", "jp", "sg", "za", "br", "mx"}


def terms():
    """(term, kind) pairs to protect, read from this machine. Short or generic words are
    dropped so the check never fires on ordinary text."""
    found = []

    def add(value, kind):
        v = str(value or "").strip()
        if len(v) >= 4 and v.lower() not in {t.lower() for t, _ in found}:
            found.append((v, kind))

    def add_email(e, kind):
        e = str(e or "").strip()
        if not e or NOREPLY.match(e):
            return
        add(e, kind)
        local, _, domain = e.partition("@")
        add(local, kind + " name")
        if domain and domain.lower() not in ("gmail.com", "outlook.com", "hotmail.com", "yahoo.com", "icloud.com", "proton.me"):
            add(domain, kind + " domain")
            # The organisation's own name, from its domain (mail.example.co.uk -> example), so a
            # bare mention such as a brand palette named after the employer is caught too.
            labels = [l for l in domain.lower().split(".") if l]
            while len(labels) > 1 and labels[-1] in _SUFFIXES:
                labels.pop()
            if labels and labels[-1] not in _SUFFIXES:
                add(labels[-1], "organization")
        for part in re.split(r"[._+-]", local):
            if len(part) >= 5:
                add(part, "name")

    try:
        with open(os.path.expanduser("~/.claude.json"), encoding="utf-8") as fh:
            acct = (json.load(fh) or {}).get("oauthAccount") or {}
    except (OSError, ValueError):
        acct = {}
    add_email(acct.get("emailAddress"), "account email")
    for key in ("fullName", "displayName"):
        add(acct.get(key), "name")
        for word in str(acct.get(key) or "").split():
            if len(word) >= 4:
                add(word, "name")
    add(acct.get("organizationName"), "organization")
    for scope in ("--global", "--local"):
        add_email(_git("config", scope, "user.email").strip(), "git email")
        name = _git("config", scope, "user.name").strip()
        if name and not re.match(r"^[a-z0-9-]+$", name):  # a GitHub handle is public; a real name is not
            add(name, "name")
    try:
        user = getpass.getuser()
    except (KeyError, OSError):
        user = ""
    if user and user not in ("runner", "root", "user", "ubuntu"):
        add(user, "system user")
        add(os.path.expanduser("~"), "home directory")
    extra = os.environ.get("SKILLDROP_PRIVATE_TERMS", "")
    path = os.path.join(ROOT, ".skilldrop-private")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            extra += "\n" + fh.read()
    for t in re.split(r"[,\n]", extra):
        t = t.strip()
        if t and not t.startswith("#"):
            add_email(t, "private term") if "@" in t else add(t, "private term")
    return found


@functools.lru_cache(maxsize=None)
def handles():
    """Public GitHub handles: the repository's owner and the handle in each noreply email.
    They are public by choice, so a name inside one (sanjay-ananth) is not a leak."""
    out = set()
    for url in _git("remote", "-v").split():
        m = re.search(r"github\.com[:/]([A-Za-z0-9-]+)/", url)
        if m:
            out.add(m.group(1))
    for scope in ("--global", "--local"):
        m = re.match(r"^(?:\d+\+)?([A-Za-z0-9-]+)@users\.noreply\.github\.com$", _git("config", scope, "user.email").strip())
        if m:
            out.add(m.group(1))
    out |= {h.strip() for h in os.environ.get("SKILLDROP_PUBLIC_HANDLES", "").split(",") if h.strip()}
    hs = sorted(out, key=len, reverse=True)
    return re.compile("|".join(r"(?<![A-Za-z0-9-])%s(?![A-Za-z0-9-])" % re.escape(h) for h in hs), re.I) if hs else None


def mask_handles(text):
    """Blank out public handles, keeping the text's length and line breaks."""
    rx = handles()
    return rx.sub(lambda m: " " * len(m.group(0)), text) if rx else text


def matcher(found):
    """One regex per kind of term; a term matches only as a whole word, so a public handle
    that contains a surname does not count as the surname."""
    return [(re.compile(r"(?<![A-Za-z0-9])%s(?![A-Za-z0-9])" % re.escape(t), re.I), k) for t, k in found]


def scan_text(text, pats, allow_names=False):
    text = mask_handles(text)
    hits = []
    for rx, kind in pats:
        if allow_names and kind == "name":
            continue
        for m in rx.finditer(text):
            line = text.count("\n", 0, m.start()) + 1
            hits.append((line, kind))
    return hits


def redact(text, pats, mark="[you]"):
    """The same text with every protected term replaced; returns (text, count)."""
    n = 0
    for rx, _ in pats:
        text, k = rx.subn(mark, text)
        n += k
    return text, n


def attribution(path):
    return any(fnmatch.fnmatch(path, p) for p in ATTRIBUTION)


def report(where, hits):
    for line, kind in hits:
        print("privacy: %s:%d contains %s" % (where, line, "your " + kind if kind != "private term" else "a private term"))


def check_identity():
    bad = []
    for var in ("GIT_AUTHOR_IDENT", "GIT_COMMITTER_IDENT"):
        ident = _git("var", var).strip()
        m = re.search(r"<([^>]*)>", ident)
        if not ident:
            print("privacy: git can't tell who is committing; set user.name and user.email "
                  "(<id>+<handle>@users.noreply.github.com)")
            return False
        if not NOREPLY.match(m.group(1) if m else ""):
            bad.append(var.split("_")[1].lower())
    for who in bad:
        print("privacy: the %s email for this commit is not a GitHub noreply address. Set it with "
              "git config user.email <id>+<handle>@users.noreply.github.com" % who)
    return not bad


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--staged", action="store_true")
    g.add_argument("--message", metavar="FILE")
    g.add_argument("--tree", action="store_true")
    g.add_argument("--commits", metavar="RANGE")
    a = ap.parse_args(argv)
    if a.commits:
        bad = 0
        for line in _git("log", "--format=%H %ae %ce", a.commits).splitlines():
            sha, ae, ce = (line.split() + ["", "", ""])[:3]
            for who, e in (("author", ae), ("committer", ce)):
                if not NOREPLY.match(e):
                    print("privacy: commit %s has a %s email that is not a GitHub noreply address" % (sha[:9], who))
                    bad += 1
        return 1 if bad else 0
    pats = matcher(terms())
    clean = True
    if a.message:
        with open(a.message, encoding="utf-8", errors="replace") as fh:
            text = "".join(l for l in fh if not l.startswith("#"))
        hits = scan_text(text, pats)
        report("commit message", hits)
        return 1 if hits else 0
    if a.staged:
        clean = check_identity()
        diff = _git("diff", "--cached", "--unified=0", "--no-color", "--diff-filter=ACMR")
        path, line = None, 0
        for row in diff.splitlines():
            if row.startswith("+++ b/"):
                path = row[6:]
            elif row.startswith("@@"):
                m = re.search(r"\+(\d+)", row)
                line = int(m.group(1)) if m else 0
            elif row.startswith("+") and not row.startswith("+++") and path:
                if not path.lower().endswith(SKIP_EXT):
                    for _, kind in scan_text(row[1:], pats, allow_names=attribution(path)):
                        report(path, [(line, kind)])
                        clean = False
                line += 1
        return 0 if clean else 1
    for path in _git("ls-files").splitlines():
        if path.lower().endswith(SKIP_EXT):
            continue
        try:
            with open(os.path.join(ROOT, path), encoding="utf-8") as fh:
                text = fh.read()
        except (OSError, UnicodeDecodeError):
            continue
        hits = scan_text(text, pats, allow_names=attribution(path))
        if hits:
            report(path, hits[:5])
            clean = False
    return 0 if clean else 1


if __name__ == "__main__":
    sys.exit(main())

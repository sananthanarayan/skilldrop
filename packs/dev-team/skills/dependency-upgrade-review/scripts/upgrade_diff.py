#!/usr/bin/env python3
"""List every dependency change in a unified diff of manifests, lockfiles and workflow files.

The mechanical layer of a dependency-upgrade review: for each changed dependency it prints
old -> new, the semver class of the jump, whether it is commit-pinned, and which file it came
from; then the packages added and removed, packages the PR title does not name, new install
scripts, native-code hints, registry or source changes, licence changes, and GitHub Actions pins
with the command that verifies each SHA. Stdlib only. It reads only the path it is given (or
stdin) and makes no network calls, so it cannot read a changelog, verify a SHA or see what CI
runs; it prints those as open checks.

Reads: package.json, package-lock.json, npm-shrinkwrap.json, yarn.lock, pnpm-lock.yaml,
requirements*.txt, constraints*.txt, pyproject.toml, Pipfile, Pipfile.lock, poetry.lock, uv.lock,
pdm.lock, go.mod, go.sum, Cargo.toml, Cargo.lock, pom.xml, build.gradle(.kts),
gradle/libs.versions.toml, .github/workflows/*.yml, action.yml, .npmrc, .yarnrc(.yml), pip.conf.

Usage:
  python3 upgrade_diff.py pr.diff [--title "Bump foo from 1.2.0 to 2.0.0"] [--format json]
  git diff origin/main...HEAD | python3 upgrade_diff.py - --title "..."
  gh pr diff 212 | python3 upgrade_diff.py -

Exit codes: 0 report printed; 2 bad input (unreadable, not a unified diff, or no dependency
files in it). The floor verdict is a minimum: the reviewer raises it on what the changelog,
the usage search and CI show, and never prints MERGE on the script's word alone.
"""
import argparse
import json
import os
import re
import sys

INSTALL_HOOKS = ("preinstall", "install", "postinstall", "prepare", "prepublish")
NATIVE_NPM = {"node-gyp", "node-gyp-build", "prebuild-install", "node-pre-gyp", "@mapbox/node-pre-gyp",
              "node-addon-api", "nan", "bindings", "cmake-js", "napi-build-utils", "@napi-rs/cli"}
NATIVE_CARGO = {"cc", "cmake", "bindgen", "pkg-config", "vcpkg"}
DEFAULT_HOSTS = {"registry.npmjs.org", "registry.yarnpkg.com", "pypi.org", "files.pythonhosted.org",
                 "index.crates.io", "github.com/rust-lang/crates.io-index", "repo.maven.apache.org",
                 "repo1.maven.org", "proxy.golang.org"}
SHA40 = re.compile(r"\b[0-9a-f]{40}\b")
JSON_SKIP_KEYS = {"", "dependencies", "devDependencies", "optionalDependencies", "peerDependencies",
                  "peerDependenciesMeta", "requires", "packages", "engines", "bin", "funding", "scripts",
                  "default", "develop", "_meta", "hash", "sources", "pipfile-spec", "overrides",
                  "directories", "repository", "exports", "os", "cpu", "workspaces", "bundleDependencies"}
TOML_SKIP_KEYS = {"name", "version", "edition", "description", "authors", "license", "license-file",
                  "readme", "rust-version", "requires-python", "build-backend", "requires", "homepage",
                  "repository", "documentation", "keywords", "categories", "publish", "resolver",
                  "python_version", "python_full_version", "url", "verify_ssl", "members", "exclude"}
PKGJSON_SKIP_KEYS = {"name", "version", "description", "main", "module", "types", "license", "author",
                     "type", "homepage", "packageManager"}
VERSIONISH = re.compile(r"^\s*(?:[\^~<>=!*]|v?\d|npm:|workspace:|latest|next|git\+|github:|https?:|file:|link:)")


# ---------------------------------------------------------------- diff parsing

def parse_diff(text):
    """Return [{path, hunks: [[(tag, line)]]}] from a unified diff (git or plain)."""
    files, cur, lines, i = [], None, text.splitlines(), 0
    while i < len(lines):
        raw = lines[i]
        if raw.startswith("diff --git "):
            m = re.match(r"diff --git a/(.+?) b/(.+)$", raw)
            cur = {"path": m.group(2) if m else raw[11:].strip(), "hunks": []}
            files.append(cur)
        elif raw.startswith("--- ") and i + 1 < len(lines) and lines[i + 1].startswith("+++ "):
            old_p = raw[4:].split("\t")[0].strip()
            new_p = lines[i + 1][4:].split("\t")[0].strip()
            path = new_p if new_p != "/dev/null" else old_p
            path = re.sub(r"^[ab]/", "", path)
            if cur is None or cur["hunks"]:
                cur = {"path": path, "hunks": []}
                files.append(cur)
            else:
                cur["path"] = path
            i += 1
        elif raw.startswith("@@") and cur is not None:
            m = re.match(r"@@ -\d+(?:,(\d+))? \+\d+(?:,(\d+))? @@", raw)
            if not m:
                i += 1
                continue
            old_n = int(m.group(1)) if m.group(1) is not None else 1
            new_n = int(m.group(2)) if m.group(2) is not None else 1
            hunk = []
            i += 1
            while i < len(lines) and (old_n > 0 or new_n > 0):
                ln = lines[i]
                if ln.startswith("\\"):
                    i += 1
                    continue
                tag, body = (ln[0], ln[1:]) if ln else (" ", "")
                if tag not in " +-":
                    break
                if tag in " -":
                    old_n -= 1
                if tag in " +":
                    new_n -= 1
                hunk.append((tag, body))
                i += 1
            cur["hunks"].append(hunk)
            continue
        i += 1
    return files


def views(hunk):
    """Old view (context + removed) and new view (context + added) of one hunk."""
    return [(t, s) for t, s in hunk if t in " -"], [(t, s) for t, s in hunk if t in " +"]


# ---------------------------------------------------------------- versions

def parse_ver(v):
    if v is None:
        return None
    v = str(v).strip().strip("\"'")
    v = v.split("@")[-1] if v.startswith("npm:") else v
    v = re.split(r"[,|\s]", v.strip())[0] if v else v
    v = re.sub(r"^(?:===|==|>=|<=|~=|!=|[\^~=<>v])+", "", v)
    m = re.match(r"^(\d+)(?:\.(\d+|x|\*))?(?:\.(\d+|x|\*))?([-+.].*)?$", v)
    if not m:
        return None
    num = lambda g: int(g) if g and g.isdigit() else 0
    return num(m.group(1)), num(m.group(2)), num(m.group(3)), (m.group(4) or "").lstrip(".")


def semver_class(old, new):
    o, n = parse_ver(old), parse_ver(new)
    if not o or not n:
        return "unknown"
    if n[:3] < o[:3]:
        return "downgrade"
    if n[0] != o[0]:
        return "major"
    if n[0] == 0 and n[1] != o[1]:
        return "minor (0.x: breaking)"
    if n[1] != o[1]:
        return "minor"
    if n[0] == 0 and n[1] == 0 and n[2] != o[2]:
        return "patch (0.0.x: breaking)"
    if n[2] != o[2]:
        return "patch"
    if n[3] != o[3]:
        return "prerelease/build"
    return "range only"


def host_of(url):
    if not url:
        return None
    url = re.sub(r"^(registry|sparse|git)\+", "", url)
    m = re.match(r"^[a-z]+://(?:[^@/]+@)?([^/:]+)", url)
    if not m:
        return url if url.startswith(("git", "file:", "link:", "github:")) else None
    host = m.group(1)
    if host == "github.com" and "crates.io-index" in url:
        return "github.com/rust-lang/crates.io-index"
    return host


# ---------------------------------------------------------------- record helpers

class Report:
    def __init__(self):
        self.changes, self.flags, self.files, self.unattributed = [], [], [], {}

    def change(self, path, eco, where, name, old, new, note=None):
        if old == new:
            return
        rec = {"file": path, "ecosystem": eco, "where": where, "name": name,
               "old": old, "new": new, "notes": [note] if note else []}
        if old is None:
            rec["kind"] = "added"
        elif new is None:
            rec["kind"] = "removed"
        else:
            rec["kind"] = "changed"
            rec["class"] = semver_class(old, new)
        if new and SHA40.search(str(new)):
            rec["notes"].append("pinned to a commit")
        p = parse_ver(new)
        if new and p and p[3] and re.search(r"(alpha|beta|rc|pre|dev|canary|next)", p[3], re.I):
            rec["notes"].append("target is a prerelease")
        for r in self.changes:
            if all(r[k] == rec[k] for k in ("file", "name", "old", "new")):
                return
        self.changes.append(rec)

    def flag(self, kind, path, text):
        f = {"kind": kind, "file": path, "text": text}
        if f not in self.flags:
            self.flags.append(f)


def pair_line_changes(rep, path, eco, where, removed, added, notes=None):
    """removed/added: {name: value}. Pair by name into changed / added / removed."""
    notes = notes or {}
    for name in list(removed) + [n for n in added if n not in removed]:
        old, new = removed.get(name), added.get(name)
        rep.change(path, eco, where, name, old, new, notes.get(name))


def scan_blocks(view, key_fn, field_res, reset_re=None):
    out, cur, loose = {}, None, []
    for tag, text in view:
        if reset_re and reset_re.match(text):
            cur = None
            continue
        k = key_fn(text)
        if k is not None:
            cur = k
            out.setdefault(k, {"tag": tag, "fields": {}})
            continue
        for f, rx in field_res.items():
            m = rx.match(text)
            if not m:
                continue
            if cur is None:
                if tag != " " and f == "version":
                    loose.append(text.strip())
            elif f not in out[cur]["fields"]:
                out[cur]["fields"][f] = (m.group(1), tag)
    return out, loose


def merge_blocks(rep, path, eco, hunks, key_fn, field_res, name_fn, reset_re=None, count_loose=True,
                 where="lockfile"):
    """Block-structured lockfiles: compare each package block's fields across the two views."""
    for hunk in hunks:
        ov, nv = views(hunk)
        old, loose_o = scan_blocks(ov, key_fn, field_res, reset_re)
        new, loose_n = scan_blocks(nv, key_fn, field_res, reset_re)
        if count_loose and (loose_o or loose_n):
            rep.unattributed[path] = rep.unattributed.get(path, 0) + max(len(loose_o), len(loose_n))
        for key in list(old) + [k for k in new if k not in old]:
            o, n = old.get(key), new.get(key)
            name, note = name_fn(key)
            of = o["fields"] if o else {}
            nf = n["fields"] if n else {}
            ov_, nv_ = of.get("version", (None,))[0], nf.get("version", (None,))[0]
            if o and not n:
                rep.change(path, eco, where, name, ov_ or "?", None, note)
                continue
            if n and not o:
                rep.change(path, eco, where, name, None, nv_ or "?", note)
            elif ov_ and nv_ and ov_ != nv_:
                rep.change(path, eco, where, name, ov_, nv_, note)
            label = f"{name} {nv_ or ''}".strip()
            for f in ("hasInstallScript", "requiresBuild"):
                if nf.get(f, (None,))[0] == "true" and of.get(f, (None,))[0] != "true":
                    rep.flag("install-script", path, f"{label}: `{f}: true` is new; the package runs code at install time")
            if nf.get("gypfile", (None,))[0] == "true" and of.get("gypfile", (None,))[0] != "true":
                rep.flag("native", path, f"{label}: `gypfile: true`, compiles native code at install")
            for f in ("resolved", "source", "url", "index", "resolution"):
                oh = host_of(of.get(f, (None,))[0]) if f != "index" else of.get(f, (None,))[0]
                nh = host_of(nf.get(f, (None,))[0]) if f != "index" else nf.get(f, (None,))[0]
                if nh and o and oh and oh != nh:
                    rep.flag("source", path, f"{label}: {f} moved from {oh} to {nh}")
                elif nh and not o and f != "index" and nh not in DEFAULT_HOSTS:
                    rep.flag("source", path, f"{label}: new package comes from {nh}, not the default registry")
            ol, nl = of.get("license", (None,))[0], nf.get("license", (None,))[0]
            if ol and nl and ol != nl:
                rep.flag("licence", path, f"{label}: licence changed from {ol} to {nl}")
            elif nl and not o:
                rep.flag("licence", path, f"{label}: new package, licence {nl}")
            for f, label_ in (("dev", "dev only"), ("optional", "optional")):
                if n and not o and nf.get(f, (None,))[0] == "true":
                    for r in rep.changes:
                        if r["file"] == path and r["name"] == name and r["kind"] == "added":
                            r["notes"].append(label_)


# ---------------------------------------------------------------- handlers

def h_package_json(rep, path, hunks):
    for hunk in hunks:
        removed, added, section = {}, {}, None
        for tag, text in hunk:
            sm = re.match(r'^\s*"(\w+)":\s*\{\s*$', text)
            if sm:
                section = sm.group(1)
                continue
            m = re.match(r'^\s*"([^"]+)":\s*"([^"]*)"', text)
            if not m or tag == " ":
                continue
            key, val = m.groups()
            if key in INSTALL_HOOKS and (section in (None, "scripts")):
                (removed if tag == "-" else added)["script:" + key] = val
                continue
            if key in PKGJSON_SKIP_KEYS or section == "scripts" or not VERSIONISH.match(val):
                continue
            (removed if tag == "-" else added)[key] = val
            if tag == "+" and re.match(r"^(git\+|github:|https?:|file:|link:)", val):
                rep.flag("source", path, f"{key}: installed from `{val}`, not the registry")
        for k in list(added):
            if k.startswith("script:"):
                hook, cmd = k[7:], added.pop(k)
                if removed.pop(k, None) != cmd:
                    rep.flag("install-script", path, f"package.json adds or changes a `{hook}` script: `{cmd}`")
        for k in list(removed):
            if k.startswith("script:"):
                removed.pop(k)
        pair_line_changes(rep, path, "npm", "manifest", removed, added)


def npm_lock_key(text):
    m = re.match(r'^\s*"([^"]*)":\s*\{\s*$', text)
    if not m or m.group(1) in JSON_SKIP_KEYS:
        return None
    return m.group(1)


def npm_lock_name(key):
    parts = key.split("node_modules/")
    name = parts[-1].rstrip("/") if len(parts) > 1 else key
    if len(parts) > 2:
        return name, f"nested copy under {parts[-2].rstrip('/')}"
    return name, None


NPM_FIELDS = {f: re.compile(rf'^\s*"{f}":\s*"?([^",]+)"?,?\s*$') for f in
              ("version", "resolved", "license", "hasInstallScript", "dev", "optional", "gypfile")}


def h_package_lock(rep, path, hunks):
    merge_blocks(rep, path, "npm", hunks, npm_lock_key, NPM_FIELDS, npm_lock_name)


def h_yarn_lock(rep, path, hunks):
    def key(text):
        m = re.match(r'^"?((?:@[^@/\s"]+/)?[^@\s",]+)@[^:]*"?:\s*$', text)
        return m.group(1) if m and not text.startswith((" ", "#")) else None
    fields = {"version": re.compile(r'^\s+version:?\s+"?([^"\s]+)"?'),
              "resolved": re.compile(r'^\s+resolved:?\s+"?([^"\s#]+)'),
              }
    merge_blocks(rep, path, "npm", hunks, key, fields, lambda k: (k, None))


def h_pnpm_lock(rep, path, hunks):
    key_re = re.compile(r"^ {2}['\"]?/?((?:@[^/@\s]+/)?[^@\s'\"/(]+)@([^\s'\"():]+)(?:\([^)]*\))*['\"]?:\s*$")

    def key(text):
        m = key_re.match(text)
        return f"{m.group(1)}\x00{m.group(2)}" if m else None
    fields = {"requiresBuild": re.compile(r"^\s+requiresBuild:\s*(true|false)"),
              "resolved": re.compile(r"^\s+resolution:\s*\{.*tarball:\s*([^\s,}]+)")}
    for hunk in hunks:
        ov, nv = views(hunk)
        old, _ = scan_blocks(ov, key, fields)
        new, _ = scan_blocks(nv, key, fields)
        removed = {k.split("\x00")[0]: k.split("\x00")[1] for k in old if k not in new}
        added = {k.split("\x00")[0]: k.split("\x00")[1] for k in new if k not in old}
        pair_line_changes(rep, path, "npm", "lockfile", removed, added)
        for k, n in new.items():
            if n["fields"].get("requiresBuild", (None,))[0] == "true" and \
                    old.get(k, {"fields": {}})["fields"].get("requiresBuild", (None,))[0] != "true":
                rep.flag("install-script", path, f"{k.replace(chr(0), ' ')}: `requiresBuild: true`, runs code at install time")
            t = n["fields"].get("resolved", (None,))[0]
            if t and k not in old and host_of(t) not in DEFAULT_HOSTS:
                rep.flag("source", path, f"{k.replace(chr(0), ' ')}: tarball from {host_of(t)}")


TOML_PKG_FIELDS = {"version": re.compile(r'^version\s*=\s*"([^"]+)"'),
                   "source": re.compile(r'^source\s*=\s*"([^"]+)"'),
                   "url": re.compile(r'^(?:url|source\s*=\s*\{\s*(?:registry|git|url))\s*=\s*"([^"]+)"')}


def h_toml_lock(eco):
    def handler(rep, path, hunks):
        def key(text):
            m = re.match(r'^name\s*=\s*"([^"]+)"', text)
            return m.group(1) if m else None
        merge_blocks(rep, path, eco, hunks, key, TOML_PKG_FIELDS,
                     lambda k: (k, None), reset_re=re.compile(r"^\[\[package\]\]"))
        if eco == "cargo":
            for r in rep.changes:
                if r["file"] == path and r["kind"] == "added" and \
                        (r["name"].endswith("-sys") or r["name"] in NATIVE_CARGO):
                    rep.flag("native", path, f"{r['name']} {r['new']}: new crate that builds or links native code")
    return handler


def h_pipfile_lock(rep, path, hunks):
    fields = {"version": re.compile(r'^\s*"version":\s*"([^"]+)"'),
              "index": re.compile(r'^\s*"index":\s*"([^"]+)"')}
    merge_blocks(rep, path, "pip", hunks, npm_lock_key, fields, lambda k: (k.lower().replace("_", "-"), None))


def h_requirements(rep, path, hunks):
    for hunk in hunks:
        removed, added = {}, {}
        for tag, text in hunk:
            if tag == " ":
                continue
            s = text.split(" #")[0].strip()
            if re.match(r"^(-i|--index-url|--extra-index-url|--find-links|-f)\b", s):
                if tag == "+":
                    rep.flag("source", path, f"package index line added: `{s}`")
                continue
            m = re.match(r"^([A-Za-z0-9][A-Za-z0-9._\-]*)(\[[^\]]*\])?\s*((?:===|==|~=|>=|<=|!=|>|<)[^;\\\s]*)", s)
            if m:
                (removed if tag == "-" else added)[m.group(1).lower().replace("_", "-")] = m.group(3)
            elif re.search(r"(git\+|https?://)", s) and tag == "+":
                rep.flag("source", path, f"requirement installed from a URL: `{s}`")
        pair_line_changes(rep, path, "pip", "manifest", removed, added)


def h_toml_manifest(eco):
    def handler(rep, path, hunks):
        for hunk in hunks:
            removed, added = {}, {}
            for tag, text in hunk:
                if tag == " ":
                    continue
                s = text.strip()
                pep = re.match(r"""^["']([A-Za-z0-9][A-Za-z0-9._\-]*)(\[[^\]]*\])?\s*([<>=!~^][^"';]*)""", s)
                if pep:
                    (removed if tag == "-" else added)[pep.group(1).lower()] = pep.group(3).strip()
                    continue
                m = re.match(r'^([A-Za-z0-9_.\-]+)\s*=\s*(?:"([^"]+)"|\{(.*)\})', s)
                if not m or m.group(1) in TOML_SKIP_KEYS:
                    continue
                name, val, table = m.group(1), m.group(2), m.group(3)
                if table is not None:
                    vm = re.search(r'\b(?:version|rev|tag|branch)\s*=\s*"([^"]+)"', table)
                    val = vm.group(1) if vm else None
                    if tag == "+" and re.search(r'\b(git|path|registry|url)\s*=', table):
                        rep.flag("source", path, f"{name}: source set in the manifest: `{{{table.strip()}}}`")
                if val and VERSIONISH.match(val) or (val and SHA40.search(val)):
                    (removed if tag == "-" else added)[name] = val
            pair_line_changes(rep, path, eco, "manifest", removed, added)
    return handler


def h_go_mod(rep, path, hunks):
    for hunk in hunks:
        removed, added, notes = {}, {}, {}
        for tag, text in hunk:
            if tag == " ":
                continue
            s = text.strip()
            if s.startswith("replace") or "=>" in s:
                if tag == "+":
                    rep.flag("source", path, f"go.mod replace directive: `{s}`")
                continue
            tm = re.match(r"^(go|toolchain)\s+(\S+)$", s)
            if tm:
                (removed if tag == "-" else added)[tm.group(1) + " (directive)"] = tm.group(2)
                continue
            m = re.match(r"^(?:require\s+)?([a-zA-Z0-9][^\s]*\.[^\s]+)\s+(v[^\s]+)(\s*//\s*indirect)?", s)
            if m:
                (removed if tag == "-" else added)[m.group(1)] = m.group(2)
                if m.group(3):
                    notes[m.group(1)] = "indirect"
        pair_line_changes(rep, path, "go", "manifest", removed, added, notes)


def h_go_sum(rep, path, hunks):
    removed, added = {}, {}
    for hunk in hunks:
        for tag, text in hunk:
            m = re.match(r"^(\S+)\s+(v[^\s/]+)(/go\.mod)?\s+h1:", text)
            if tag == " " or not m or m.group(3):
                continue
            (removed if tag == "-" else added)[m.group(1)] = m.group(2)
    pair_line_changes(rep, path, "go", "lockfile", removed, added)


def h_pom(rep, path, hunks):
    def key(text):
        m = re.match(r"^\s*<artifactId>([^<]+)</artifactId>", text)
        return m.group(1) if m else None
    fields = {"version": re.compile(r"^\s*<version>([^<]+)</version>")}
    merge_blocks(rep, path, "maven", hunks, key, fields, lambda k: (k, None), where="manifest")
    for hunk in hunks:
        removed, added = {}, {}
        for tag, text in hunk:
            if tag == " ":
                continue
            m = re.match(r"^\s*<([\w.\-]+\.version)>([^<]+)</", text)
            if m:
                (removed if tag == "-" else added)[m.group(1)] = m.group(2)
            if tag == "+" and re.match(r"^\s*<url>", text):
                rep.flag("source", path, f"repository url line added: `{text.strip()}`")
        pair_line_changes(rep, path, "maven", "manifest", removed, added)


def h_gradle(rep, path, hunks):
    for hunk in hunks:
        removed, added = {}, {}
        for tag, text in hunk:
            if tag == " ":
                continue
            m = re.search(r"""["']([\w.\-]+:[\w.\-]+):([\w.\-+]+)["']""", text)
            if m:
                (removed if tag == "-" else added)[m.group(1)] = m.group(2)
        pair_line_changes(rep, path, "gradle", "manifest", removed, added)


def h_registry_config(rep, path, hunks):
    for hunk in hunks:
        for tag, text in hunk:
            if tag == "+" and re.search(r"(registry|index-url|extra-index-url|npmRegistryServer|scope)", text, re.I):
                rep.flag("source", path, f"registry configuration changed: `{text.strip()}`")


def h_workflow(rep, path, hunks):
    uses = re.compile(r"""^\s*-?\s*uses:\s*['"]?([^@\s'"]+)@([^\s'"#]+)['"]?\s*(?:#\s*(.*))?$""")
    for hunk in hunks:
        removed, added = {}, {}
        for tag, text in hunk:
            m = uses.match(text)
            if tag == " " or not m or m.group(1).startswith(("./", "docker://")):
                continue
            (removed if tag == "-" else added)[m.group(1)] = (m.group(2), (m.group(3) or "").strip())
        for name in list(removed) + [n for n in added if n not in removed]:
            o, n = removed.get(name), added.get(name)
            if o == n:
                continue
            show = lambda x: (f"{x[0][:12]}… ({x[1]})" if SHA40.fullmatch(x[0]) and x[1]
                              else (f"{x[0][:12]}…" if SHA40.fullmatch(x[0]) else x[0])) if x else None
            ver = lambda x: (x[1] or None) if x and SHA40.fullmatch(x[0]) else (x[0] if x else None)
            rec_old, rec_new = show(o), show(n)
            rep.change(path, "github-actions", "workflow", name, rec_old, rec_new)
            r = next(r for r in rep.changes if r["file"] == path and r["name"] == name and r["new"] == rec_new)
            if o and n:
                r["class"] = semver_class(ver(o), ver(n))
            repo = "/".join(name.split("/")[:2])
            if n and SHA40.fullmatch(n[0]):
                tag_ = re.match(r"^(v?[\w.\-]+)", n[1]).group(1) if n[1] else None
                if tag_:
                    rep.flag("pin", path, f"{name}@{n[0]} claims {tag_}. UNVERIFIED until the tag resolves to this commit: "
                                          f"`git ls-remote https://github.com/{repo} refs/tags/{tag_} 'refs/tags/{tag_}^{{}}'` "
                                          f"(the `^{{}}` line is the commit for an annotated tag; it must equal {n[0]})")
                else:
                    rep.flag("pin", path, f"{name}@{n[0]} has no version comment, so which release it is cannot be read "
                                          f"from the diff. UNVERIFIED: `git ls-remote --tags https://github.com/{repo}` and find {n[0]}")
                if o and not SHA40.fullmatch(o[0]):
                    r["notes"].append("pin strengthened from tag to SHA")
            elif n:
                kind = "branch" if n[0] in ("main", "master", "develop", "trunk") or not re.match(r"^v?\d", n[0]) else "tag"
                rep.flag("pin", path, f"{name}@{n[0]} is a {kind}-only pin: the {kind} can be moved to other code after "
                                      f"review. Pin to the commit: `git ls-remote https://github.com/{repo} refs/tags/{n[0]} "
                                      f"'refs/tags/{n[0]}^{{}}'`" if kind == "tag" else
                         f"{name}@{n[0]} tracks a branch: every run gets whatever was pushed last. Pin to a release commit")
                if o and SHA40.fullmatch(o[0]):
                    r["notes"].append("pin WEAKENED from SHA to " + kind)


def handler_for(path):
    base = os.path.basename(path)
    low = path.replace("\\", "/")
    if re.search(r"(^|/)\.github/workflows/[^/]+\.ya?ml$", low) or base in ("action.yml", "action.yaml"):
        return h_workflow
    table = {
        "package.json": h_package_json, "package-lock.json": h_package_lock,
        "npm-shrinkwrap.json": h_package_lock, "yarn.lock": h_yarn_lock, "pnpm-lock.yaml": h_pnpm_lock,
        "pyproject.toml": h_toml_manifest("pip"), "Pipfile": h_toml_manifest("pip"),
        "Pipfile.lock": h_pipfile_lock, "poetry.lock": h_toml_lock("pip"), "uv.lock": h_toml_lock("pip"),
        "pdm.lock": h_toml_lock("pip"), "go.mod": h_go_mod, "go.sum": h_go_sum,
        "Cargo.toml": h_toml_manifest("cargo"), "Cargo.lock": h_toml_lock("cargo"), "pom.xml": h_pom,
        "build.gradle": h_gradle, "build.gradle.kts": h_gradle, "libs.versions.toml": h_toml_manifest("gradle"),
        ".npmrc": h_registry_config, ".yarnrc": h_registry_config, ".yarnrc.yml": h_registry_config,
        "pip.conf": h_registry_config,
    }
    if base in table:
        return table[base]
    if re.match(r"^(requirements|constraints)[\w.\-]*\.(txt|in)$", base):
        return h_requirements
    return None


# ---------------------------------------------------------------- analysis + output

def analyse(files, title):
    rep = Report()
    for f in files:
        h = handler_for(f["path"])
        rep.files.append((f["path"], h is not None))
        if h:
            h(rep, f["path"], f["hunks"])
    manifest_recs = {(r["ecosystem"], r["name"], r["old"], r["new"]) for r in rep.changes if r["where"] == "manifest"}
    rep.changes = [r for r in rep.changes if r["where"] != "lockfile" or
                   (r["ecosystem"], r["name"], r["old"], r["new"]) not in manifest_recs]
    manifest_names = {r["name"] for r in rep.changes if r["where"] in ("manifest", "workflow")}
    for r in rep.changes:
        if r["where"] == "lockfile":
            r["notes"].insert(0, "direct" if r["name"] in manifest_names else "lockfile only (transitive)")
        if r["kind"] == "added" and r["ecosystem"] == "npm" and r["name"] in NATIVE_NPM:
            rep.flag("native", r["file"], f"{r['name']} {r['new']}: new package used to build or fetch native binaries")
    if title:
        t = title.lower()
        for r in rep.changes:
            short = r["name"].split("/")[-1].lower()
            r["in_title"] = r["name"].lower() in t or (len(short) > 3 and re.search(rf"\b{re.escape(short)}\b", t) is not None)
    reasons_stop, reasons_check = [], []
    for fl in rep.flags:
        if fl["kind"] in ("install-script", "source"):
            reasons_stop.append(f"{fl['kind']}: {fl['text']}")
        elif fl["kind"] == "pin":
            reasons_check.append("pin: " + fl["text"].split(". ")[0])
        elif not (fl["kind"] == "licence" and "new package" in fl["text"]):
            reasons_check.append(f"{fl['kind']}: {fl['text']}")
    locked = {r["name"] for r in rep.changes if r["where"] == "lockfile"}
    for r in rep.changes:
        if r["where"] == "manifest" and r["name"] in locked:
            continue
        cls = r.get("class", "")
        if cls in ("major", "minor (0.x: breaking)", "patch (0.0.x: breaking)", "downgrade", "unknown"):
            reasons_check.append(f"{cls}: {r['name']} {r['old']} -> {r['new']}")
        if r["kind"] == "added":
            reasons_check.append(f"added: {r['name']} {r['new']}")
        if "target is a prerelease" in r["notes"] or any("WEAKENED" in n for n in r["notes"]):
            reasons_check.append(f"{r['name']}: {', '.join(r['notes'])}")
    if rep.unattributed:
        reasons_check.append("version lines with no package name in context: " +
                             ", ".join(f"{p} ({n})" for p, n in rep.unattributed.items()))
    reasons_stop = list(dict.fromkeys(reasons_stop))
    reasons_check = list(dict.fromkeys(reasons_check))
    if reasons_stop:
        floor = "DO NOT MERGE"
    elif reasons_check:
        floor = "MERGE AFTER CHECKS"
    else:
        floor = "none from the diff"
    return rep, floor, reasons_stop, reasons_check


def render_md(rep, floor, stop, check, title):
    out = ["# Dependency upgrade diff", ""]
    read = [p for p, ok in rep.files if ok]
    skipped = [p for p, ok in rep.files if not ok]
    out.append("Files read: " + (", ".join(f"`{p}`" for p in read) or "none"))
    if skipped:
        out.append("Other files in the diff (not dependency files, review them separately): " +
                   ", ".join(f"`{p}`" for p in skipped))
    if title:
        out.append(f'PR title: "{title}"')
    out += ["", f"**Floor verdict: {floor}** (mechanical; the changelog, usage and CI checks are still to do, "
            "and only they can make it MERGE)"]
    if stop or check:
        out.append("")
    for r in stop:
        out.append(f"- STOP {r}")
    for r in check:
        out.append(f"- CHECK {r}")
    groups = (("Changed", "changed"), ("Added", "added"), ("Removed", "removed"))
    for heading, kind in groups:
        rows = [r for r in rep.changes if r["kind"] == kind]
        out += ["", f"## {heading} ({len(rows)})", ""]
        if not rows:
            out.append("None.")
            continue
        out.append("| Package | Ecosystem | Old → New | Class | File | Notes |")
        out.append("|---|---|---|---|---|---|")
        for r in rows:
            notes = list(r["notes"])
            if title and not r.get("in_title"):
                notes.append("not named in the title")
            out.append(f"| `{r['name']}` | {r['ecosystem']} | {r['old'] or '—'} → {r['new'] or '—'} | "
                       f"{r.get('class', '—')} | `{r['file']}` | {'; '.join(notes) or ''} |")
    if title:
        beyond = [r for r in rep.changes if not r.get("in_title")]
        out += ["", f"## Beyond the title ({len(beyond)})", ""]
        out += [f"- `{r['name']}` {r['kind']}: {r['old'] or '—'} → {r['new'] or '—'} ({r['file']})" for r in beyond] or ["None."]
    labels = (("install-script", "Install scripts"), ("native", "Native code"), ("source", "Sources and registries"),
              ("licence", "Licences"), ("pin", "Pins (verify every SHA; the script cannot)"))
    for kind, heading in labels:
        rows = [f for f in rep.flags if f["kind"] == kind]
        out += ["", f"## {heading} ({len(rows)})", ""]
        out += [f"- `{f['file']}`: {f['text']}" for f in rows] or ["None seen in the diff."]
    if rep.unattributed:
        out += ["", "## Out of context", ""]
        out += [f"- `{p}`: {n} changed version line(s) with the package name outside the hunk. "
                f"Re-run on `git diff -U12` to attribute them." for p, n in rep.unattributed.items()]
    out += ["", "## Not visible in a diff", "",
            "- The release notes for every version between old and new, and what they break, deprecate, fix or relicense.",
            "- Whether the repo calls an API those notes change or remove.",
            "- Whether any CI job runs the code paths that use the changed packages.",
            "- Publisher or maintainer changes, unless the lockfile records them.", ""]
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("diff", help="unified diff file, or - for stdin")
    ap.add_argument("--title", help="the PR title, to list changes it does not name")
    ap.add_argument("--format", choices=("md", "json"), default="md")
    ap.add_argument("-o", "--output", help="write the report here instead of stdout")
    a = ap.parse_args(argv)
    try:
        text = sys.stdin.read() if a.diff == "-" else open(a.diff, encoding="utf-8", errors="replace").read()
    except OSError as e:
        print(f"upgrade_diff: cannot read {a.diff}: {e}", file=sys.stderr)
        return 2
    files = parse_diff(text)
    if not files:
        print("upgrade_diff: no unified diff found in the input (expected `diff --git` or ---/+++ headers)", file=sys.stderr)
        return 2
    if not any(handler_for(f["path"]) for f in files):
        print("upgrade_diff: the diff touches no manifest, lockfile or workflow file this script reads: " +
              ", ".join(f["path"] for f in files), file=sys.stderr)
        return 2
    rep, floor, stop, check = analyse(files, a.title)
    if a.format == "json":
        body = json.dumps({"floor_verdict": floor, "stop": stop, "check": check, "changes": rep.changes,
                           "flags": rep.flags, "unattributed": rep.unattributed,
                           "files": [{"path": p, "read": ok} for p, ok in rep.files]}, indent=2)
    else:
        body = render_md(rep, floor, stop, check, a.title)
    if a.output:
        with open(a.output, "w", encoding="utf-8") as fh:
            fh.write(body + "\n")
    else:
        print(body)
    return 0


if __name__ == "__main__":
    sys.exit(main())

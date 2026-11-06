#!/usr/bin/env python3
"""Size a JavaScript bundle from the bundler's stats file and say what pulls each module in. Stdlib only.

Reads one of these, detected from its keys:
  - webpack stats JSON (`webpack --json > stats.json`): assets, chunks (initial / entry),
    modules with name, size, chunks and reasons, entrypoints. Multi-compiler output
    (`children`) uses the first child.
  - esbuild metafile (`--metafile=meta.json`): inputs with imports; outputs with bytes,
    entryPoint, imports (import-statement / dynamic-import) and inputs[].bytesInOutput.
  - rollup-plugin-visualizer raw data (`template: "raw-data"`, also what Vite uses):
    tree, nodeParts (renderedLength, gzipLength, brotliLength) and nodeMetas
    (id, moduleParts, imported, importedBy, isEntry).

It prints, per entry, the initial JavaScript (what blocks first render) and the lazy chunks;
the largest modules; packages by size; packages installed at more than one path, with what
pulls each copy in; mechanical flags (whole-library CommonJS imports, locale bundles,
polyfills, modules in several chunks); and, with --why, the import chain from an entry to a
module or package. With --compare it diffs two stats files by entry, chunk, package and module.

It also reads the project around the stats file (the first of the stats folder, its parent or
grandparent that holds package.json, .browserslistrc or src/; or --root): package.json
(dependency ranges, browserslist), .browserslistrc, the lockfile (installed versions and the
range each dependent declares), bundler and TypeScript configs (target, existing budgets), and
the source files on disk that import the bundled packages. It prints what it found and what is
absent, and checks each bundled core-js polyfill against the browser targets.

Every size is in bytes (kB = 1000 bytes), exactly as the stats give them. Compressed sizes are
printed only when measured: "built-file" gzips the emitted files found under --dist (level 9);
"visualizer" sums the plugin's per-module gzip/brotli lengths. Nothing is estimated.

Usage:
  python3 bundle_stats.py stats.json [--why lodash] [--budget main=170kB] [--dist dist/] [--root .]
  python3 bundle_stats.py --compare before.json after.json [--budget main=200000] [--json]
  cat stats.json | python3 bundle_stats.py - --json -o report.json

A budget is ENTRY=SIZE on the entry's initial JavaScript in the stats' own size (bytes, or
with a kB / KiB suffix), or ENTRY=gzip:SIZE when compressed sizes are measured.

Exit codes: 0 report written; 1 a --budget was exceeded; 2 bad input.
"""
import argparse
import gzip
import json
import os
import re
import sys
from collections import defaultdict, deque

KIB = 1024.0
KB = 1000.0
JS_EXT = (".js", ".mjs", ".cjs")
CSS_EXT = (".css",)

POLYFILL_PACKAGES = {
    "core-js", "core-js-pure", "@babel/polyfill", "regenerator-runtime", "whatwg-fetch",
    "promise-polyfill", "es6-promise", "intersection-observer", "resize-observer-polyfill",
    "url-polyfill", "url-search-params-polyfill", "abortcontroller-polyfill",
    "smoothscroll-polyfill", "formdata-polyfill", "element-closest", "custom-event-polyfill",
    "@webcomponents/webcomponentsjs", "web-streams-polyfill", "unfetch", "isomorphic-fetch",
}

HASH_RE = re.compile(r"[.-]([A-Za-z0-9_-]{8,}|[0-9a-f]{6,})(?=\.(?:m?js|cjs|css)$)")
PNPM_RE = re.compile(r"\.pnpm/(@[^/+]+\+[^/@]+|[^/@]+)@([0-9][^/_(]*)")
YARN_RE = re.compile(r"([^/]+)-npm-([0-9][^/]*?)-[0-9a-f]{6,}-[0-9a-f]{6,}\.zip")
CONCAT_RE = re.compile(r" \+ \d+ modules?$")


class InputError(Exception):
    pass


# ---------------------------------------------------------------- helpers

def kib(n):
    """Exact bytes, one unit system throughout: 163,000 B."""
    if n is None:
        return "n/a"
    return "{:,} B".format(int(round(n)))


def bkb(n):
    """Exact bytes with the kB (1000 bytes) figure: 163,000 B (163.0 kB)."""
    if n is None:
        return "not measured"
    return "{:,} B ({:.1f} kB)".format(int(round(n)), n / KB)


def clean_path(p):
    if p is None:
        return ""
    p = str(p).replace("\\", "/")
    p = p.lstrip("\0")
    p = CONCAT_RE.sub("", p)
    if "!" in p:
        p = p.split("!")[-1]
    p = p.split("?")[0]
    while p.startswith("./"):
        p = p[2:]
    return p.lstrip("/")


def strip_hash(name):
    def repl(m):
        h = m.group(1)
        looks_hash = (any(c.isdigit() for c in h) or (h.lower() != h and h.upper() != h)
                      or re.fullmatch(r"[0-9a-f]{6,}", h) is not None)
        return "" if looks_hash else m.group(0)
    return HASH_RE.sub(repl, name)


def package_of(path):
    """(name, install_path, version or None) for a node_modules path, else None."""
    idx = path.rfind("node_modules/")
    if idx < 0:
        return None
    rest = path[idx + len("node_modules/"):]
    parts = rest.split("/")
    if not parts or not parts[0] or parts[0].startswith("."):
        return None
    if parts[0].startswith("@") and len(parts) > 1:
        name = parts[0] + "/" + parts[1]
    else:
        name = parts[0]
    install = path[:idx] + "node_modules/" + name
    prefix = path[:idx]
    version = None
    found = PNPM_RE.findall(prefix)
    if found:
        seg_name, seg_ver = found[-1]
        if seg_name.replace("+", "/") == name:
            version = seg_ver
    if version is None:
        found = YARN_RE.findall(prefix)
        if found:
            seg_name, seg_ver = found[-1]
            if seg_name == name.replace("/", "-").lstrip("@") or seg_name == name.replace("/", "-"):
                version = seg_ver
    return name, install, version


def owner_label(path):
    pkg = package_of(path)
    return pkg[0] if pkg else path


def is_js(f):
    return f.lower().endswith(JS_EXT)


def is_css(f):
    return f.lower().endswith(CSS_EXT)


def stem(name):
    base = os.path.basename(strip_hash(name))
    return base.rsplit(".", 1)[0] if "." in base else base


def new_bundle(fmt, tool):
    return {"format": fmt, "tool": tool, "notes": [], "modules": {}, "edges": [],
            "chunks": {}, "entries": {}, "entry_modules": set(), "cjs_paths": set(),
            "raw_basis": "", "module_basis": ""}


def add_module(b, key, size=0, chunk=None, source=None):
    m = b["modules"].get(key)
    if m is None:
        m = {"path": key, "size": 0, "chunks": set(), "source": None, "cjs": False,
             "chunk_sizes": defaultdict(int)}
        b["modules"][key] = m
    m["size"] += size
    if chunk is not None:
        m["chunks"].add(chunk)
        m["chunk_sizes"][chunk] += size
    if source is not None and m["source"] is None:
        m["source"] = source
    return m


def new_chunk(b, key, name, files, initial, entry):
    ch = {"key": key, "name": name, "files": list(files), "raw": 0, "css_raw": 0,
          "initial": initial, "entry": entry, "loaded_from": [], "vis_gzip": None,
          "vis_brotli": None, "raw_from_modules": False}
    b["chunks"][key] = ch
    return ch


def unique_key(existing, key):
    if key not in existing:
        return key
    i = 2
    while "%s#%d" % (key, i) in existing:
        i += 1
    return "%s#%d" % (key, i)


# ---------------------------------------------------------------- webpack

def load_webpack(data):
    if not data.get("modules") and not data.get("chunks") and isinstance(data.get("children"), list) and data["children"]:
        child = data["children"][0]
        b = load_webpack(child)
        b["notes"].append("multi-compiler stats: only the first child (%s) is read"
                          % (child.get("name") or "unnamed"))
        return b
    tool = "webpack %s" % data.get("version", "").strip() if data.get("version") else "webpack"
    b = new_bundle("webpack", tool.strip())
    assets = {}
    for a in data.get("assets") or []:
        if isinstance(a, dict) and a.get("name"):
            assets[a["name"]] = a.get("size") or 0
    id_to_key = {}
    for c in data.get("chunks") or []:
        names = c.get("names") or []
        files = [f for f in (c.get("files") or []) if not f.endswith(".map") and ".hot-update." not in f]
        if names:
            key = names[0]
        elif files:
            key = strip_hash(files[0])
        else:
            key = "chunk %s" % c.get("id")
        key = unique_key(b["chunks"], key)
        id_to_key[c.get("id")] = key
        ch = new_chunk(b, key, names[0] if names else key, files, bool(c.get("initial")), bool(c.get("entry")))
        js_files = [f for f in files if is_js(f)]
        if js_files and all(f in assets for f in js_files):
            ch["raw"] = sum(assets[f] for f in js_files)
        else:
            ch["raw"] = c.get("size") or 0
            ch["raw_from_modules"] = True
        ch["css_raw"] = sum(assets.get(f, 0) for f in files if is_css(f))
        for o in c.get("origins") or []:
            mn = o.get("moduleName")
            if mn and not ch["initial"]:
                ch["loaded_from"].append(clean_path(mn))
    raw_modules = list(data.get("modules") or [])
    if not raw_modules:
        for c in data.get("chunks") or []:
            for m in c.get("modules") or []:
                m = dict(m)
                m.setdefault("chunks", [c.get("id")])
                raw_modules.append(m)

    def walk(m, inherited_chunks):
        name = m.get("name") or m.get("identifier") or ""
        mtype = m.get("moduleType") or ""
        if mtype == "runtime" or name.startswith("webpack/runtime") or name.startswith("external "):
            return
        chunks = m.get("chunks")
        if chunks is None:
            chunks = inherited_chunks
        nested = m.get("modules") or []
        if nested:
            for n in nested:
                walk(n, chunks)
            return
        key = clean_path(name)
        if not key:
            return
        size = m.get("size") or 0
        ckeys = [id_to_key[c] for c in chunks if c in id_to_key] or [None]
        for ck in ckeys:
            add_module(b, key, size, ck, m.get("source") if isinstance(m.get("source"), str) else None)
        mod = b["modules"][key]
        mod["size"] = size  # a module in several chunks is one module; chunk_sizes holds the copies
        bail = " ".join(m.get("optimizationBailout") or [])
        if "not an ECMAScript module" in bail or mtype == "javascript/dynamic" or (
                "providedExports" in m and m.get("providedExports") is None and mtype != "javascript/esm"
                and key.endswith(JS_EXT)):
            mod["cjs"] = True
        for r in m.get("reasons") or []:
            rtype = (r.get("type") or "").lower()
            src = r.get("moduleName") or r.get("resolvedModule")
            if "entry" in rtype or not src:
                if "entry" in rtype:
                    b["entry_modules"].add(key)
                continue
            kind = "dynamic" if "import()" in rtype or "dynamic" in rtype else "static"
            if "cjs" in rtype or "require" in rtype:
                kind = "static"
            b["edges"].append((clean_path(src), key, kind, r.get("userRequest")))
        if m.get("depth") == 0:
            b["entry_modules"].add(key)

    for m in raw_modules:
        walk(m, [])

    eps = data.get("entrypoints") or {}
    if eps:
        for name, ep in eps.items():
            ckeys = [id_to_key[c] for c in (ep.get("chunks") or []) if c in id_to_key]
            b["entries"][name] = {"chunks": ckeys}
    else:
        for ch in b["chunks"].values():
            if ch["entry"]:
                b["entries"][ch["name"]] = {"chunks": [ch["key"]]}
    from_mods = [ch for ch in b["chunks"].values() if ch["raw_from_modules"]]
    if from_mods and len(from_mods) == len(b["chunks"]):
        b["raw_basis"] = "webpack chunk size = sum of module sizes, before minification (the stats have no assets)"
    elif from_mods:
        b["notes"].append("some chunks have no emitted-asset size in the stats; their size is the sum of module sizes before minification")
        b["raw_basis"] = "emitted asset bytes (after minification) where the stats list the asset"
    else:
        b["raw_basis"] = "emitted asset bytes (after minification, before compression)"
    b["module_basis"] = "webpack module size, before minification"
    return b


# ---------------------------------------------------------------- esbuild

def load_esbuild(data):
    b = new_bundle("esbuild", "esbuild metafile")
    inputs = data.get("inputs") or {}
    outputs = {k: v for k, v in (data.get("outputs") or {}).items() if not k.endswith(".map")}
    dynamic_targets = set()
    for ipath, inp in inputs.items():
        src = clean_path(ipath)
        if (inp.get("format") or "") == "cjs":
            b["cjs_paths"].add(src)
        for imp in inp.get("imports") or []:
            if imp.get("external") or not imp.get("path"):
                continue
            kind = imp.get("kind") or ""
            if kind in ("import-rule", "url-token", "composes-from"):
                continue
            k = "dynamic" if kind == "dynamic-import" else "static"
            dst = clean_path(imp["path"])
            if k == "dynamic":
                dynamic_targets.add(dst)
            b["edges"].append((src, dst, k, imp.get("original")))
    out_key = {}
    for oname, out in outputs.items():
        if is_css(oname):
            continue  # a CSS output is counted on the JS output that names it as cssBundle
        ep = clean_path(out.get("entryPoint")) if out.get("entryPoint") else None
        if ep:
            key = ep
        else:
            biggest = max((out.get("inputs") or {}).items(), key=lambda kv: kv[1].get("bytesInOutput", 0), default=None)
            key = "shared chunk: " + (owner_label(clean_path(biggest[0])) if biggest else strip_hash(oname))
        key = unique_key(b["chunks"], key)
        out_key[oname] = key
        is_lazy = bool(ep) and ep in dynamic_targets
        ch = new_chunk(b, key, os.path.basename(oname), [oname], False, bool(ep) and not is_lazy)
        ch["raw"] = out.get("bytes") or 0
        ch["dyn_entry"] = is_lazy
        for ipath, info in (out.get("inputs") or {}).items():
            add_module(b, clean_path(ipath), info.get("bytesInOutput") or 0, key)
    for oname, out in outputs.items():
        key = out_key.get(oname)
        if key and out.get("cssBundle") and out["cssBundle"] in outputs:
            b["chunks"][key]["css_raw"] = outputs[out["cssBundle"]].get("bytes") or 0
    # initial closure per entry over static output imports
    for oname, out in outputs.items():
        key = out_key.get(oname)
        if not key or not b["chunks"][key]["entry"] or is_css(oname):
            continue
        seen = [key]
        stack = [oname]
        while stack:
            cur = stack.pop()
            for imp in outputs.get(cur, {}).get("imports") or []:
                if imp.get("external") or imp.get("kind") == "dynamic-import":
                    continue
                k2 = out_key.get(imp.get("path"))
                if k2 and k2 not in seen:
                    seen.append(k2)
                    stack.append(imp["path"])
        ep = clean_path(out["entryPoint"])
        b["entries"][ep] = {"chunks": seen}
        b["entry_modules"].add(ep)
    initial = set(k for e in b["entries"].values() for k in e["chunks"])
    for k, ch in b["chunks"].items():
        ch["initial"] = k in initial
    for src, dst, kind, _ in b["edges"]:
        if kind == "dynamic":
            for ch in b["chunks"].values():
                if ch.get("dyn_entry") and ch["key"] == dst:
                    ch["loaded_from"].append(src)
    for p in b["cjs_paths"]:
        if p in b["modules"]:
            b["modules"][p]["cjs"] = True
    b["raw_basis"] = "output file bytes (minified if --minify was on; before compression; .map files left out)"
    b["module_basis"] = "esbuild bytesInOutput (bytes each input contributes to the output)"
    return b


# ---------------------------------------------------------------- rollup-plugin-visualizer

def load_rollup(data):
    if data.get("version") not in (None, 2, 3):
        raise InputError("rollup-plugin-visualizer data version %r is not supported (expected 2)" % data.get("version"))
    b = new_bundle("rollup-visualizer", "rollup-plugin-visualizer raw data")
    env = data.get("env") or {}
    if env.get("rollup"):
        b["tool"] = "rollup %s (visualizer raw data)" % env["rollup"]
    opts = data.get("options") or {}
    parts = data.get("nodeParts") or {}
    metas = data.get("nodeMetas") or {}
    uid_to_key = {}
    file_key = {}
    files = []
    for c in (data.get("tree") or {}).get("children") or []:
        if c.get("name"):
            files.append(c["name"])
    for meta in metas.values():
        for f in (meta.get("moduleParts") or {}):
            if f not in files:
                files.append(f)
    for f in files:
        key = unique_key(b["chunks"], strip_hash(f))
        file_key[f] = key
        new_chunk(b, key, f, [f], False, False)
    gz_on = bool(opts.get("gzip"))
    br_on = bool(opts.get("brotli"))
    for uid, meta in metas.items():
        raw_id = str(meta.get("id") or "")
        key = clean_path(raw_id)
        uid_to_key[uid] = key
        if "?commonjs" in raw_id:
            b["cjs_paths"].add(key)
        if meta.get("isExternal"):
            continue
        if meta.get("isEntry"):
            b["entry_modules"].add(key)
        for f, puid in (meta.get("moduleParts") or {}).items():
            part = parts.get(puid) or {}
            ck = file_key.get(f)
            mod = add_module(b, key, part.get("renderedLength") or 0, ck)
            if gz_on:
                mod["gzip"] = (mod.get("gzip") or 0) + (part.get("gzipLength") or 0)
            ch = b["chunks"][ck]
            ch["raw"] += part.get("renderedLength") or 0
            if gz_on:
                ch["vis_gzip"] = (ch["vis_gzip"] or 0) + (part.get("gzipLength") or 0)
            if br_on:
                ch["vis_brotli"] = (ch["vis_brotli"] or 0) + (part.get("brotliLength") or 0)
    for uid, meta in metas.items():
        src = uid_to_key[uid]
        for imp in meta.get("imported") or []:
            dst = uid_to_key.get(imp.get("uid"))
            if dst is None or dst == src:
                continue
            if (metas.get(imp.get("uid")) or {}).get("isExternal"):
                continue
            b["edges"].append((src, dst, "dynamic" if imp.get("dynamic") else "static", None))
    static_fwd = defaultdict(list)
    for s, d, k, _ in b["edges"]:
        if k == "static":
            static_fwd[s].append(d)
    dyn_targets = set(d for s, d, k, _ in b["edges"] if k == "dynamic")
    for em in sorted(b["entry_modules"]):
        if em in dyn_targets or em not in b["modules"]:
            continue
        seen = {em}
        q = deque([em])
        while q:
            cur = q.popleft()
            for d in static_fwd.get(cur, []):
                if d not in seen:
                    seen.add(d)
                    q.append(d)
        ckeys = []
        for mk in seen:
            for ck in (b["modules"].get(mk) or {}).get("chunks", ()):
                if ck and ck not in ckeys:
                    ckeys.append(ck)
        own = sorted(b["modules"][em]["chunks"])
        ckeys = own + sorted(c for c in ckeys if c not in own)
        b["entries"][em] = {"chunks": ckeys}
        for ck in own:
            b["chunks"][ck]["entry"] = True
    b["entry_modules"] -= dyn_targets
    initial = set(k for e in b["entries"].values() for k in e["chunks"])
    for k, ch in b["chunks"].items():
        ch["initial"] = k in initial
        if not ch["initial"]:
            members = set(mk for mk, m in b["modules"].items() if k in m["chunks"])
            for s, d, kind, _ in b["edges"]:
                if kind == "dynamic" and d in members and s not in members and s not in ch["loaded_from"]:
                    ch["loaded_from"].append(s)
    for p in b["cjs_paths"]:
        if p in b["modules"]:
            b["modules"][p]["cjs"] = True
    b["raw_basis"] = "rendered length (after tree-shaking; before minification unless the visualizer runs after the minifier)"
    b["module_basis"] = "rendered length per module"
    if not gz_on:
        b["notes"].append("the visualizer was run without gzipSize, so no compressed sizes are available")
    return b


# ---------------------------------------------------------------- load

def load(path):
    try:
        if path == "-":
            text = sys.stdin.read()
        else:
            with open(path, "r", encoding="utf-8-sig") as fh:
                text = fh.read()
    except OSError as e:
        raise InputError("cannot read %s: %s" % (path, e))
    except UnicodeDecodeError:
        raise InputError("%s is not UTF-8 text; save it as UTF-8" % path)
    if not text.strip():
        raise InputError("%s is empty" % path)
    try:
        data = json.loads(text)
    except ValueError as e:
        raise InputError("%s is not JSON (%s). webpack prints build logs before the JSON unless run with --json > stats.json" % (path, e))
    if not isinstance(data, dict):
        raise InputError("%s is JSON but not an object" % path)
    if "lighthouseVersion" in data:
        raise InputError("%s is a Lighthouse report, not bundler stats" % path)
    if "nodeMetas" in data and "nodeParts" in data:
        b = load_rollup(data)
    elif isinstance(data.get("inputs"), dict) and isinstance(data.get("outputs"), dict):
        b = load_esbuild(data)
    elif any(k in data for k in ("modules", "chunks", "assets", "entrypoints")) or isinstance(data.get("children"), list):
        b = load_webpack(data)
    else:
        raise InputError("%s is not a webpack stats file, an esbuild metafile or rollup-plugin-visualizer raw data" % path)
    if not b["modules"] and not b["chunks"]:
        raise InputError("%s has no modules or chunks to size" % path)
    rev = defaultdict(list)
    for s, d, k, r in b["edges"]:
        if s != d:
            rev[d].append((s, k, r))
    b["rev"] = rev
    for ch in b["chunks"].values():
        if ch["initial"] or ch["loaded_from"]:
            continue
        members = set(mk for mk, m in b["modules"].items() if ch["key"] in m["chunks"])
        for s, d, k, _ in b["edges"]:
            if k == "dynamic" and d in members and s not in members and s not in ch["loaded_from"]:
                ch["loaded_from"].append(s)
    if not b["entry_modules"]:
        b["entry_modules"] = set(mk for mk in b["modules"] if mk not in rev)
        b["notes"].append("no entry modules are marked; chains start at modules nothing imports")
    return b


# ---------------------------------------------------------------- analysis

def compress_chunk(b, ch, dist):
    js_files = [f for f in ch["files"] if is_js(f)]
    if dist and js_files:
        total = 0
        ok = True
        for f in js_files:
            cand = [os.path.join(dist, f), os.path.join(dist, os.path.basename(f))]
            hit = next((c for c in cand if os.path.isfile(c)), None)
            if not hit:
                ok = False
                break
            with open(hit, "rb") as fh:
                total += len(gzip.compress(fh.read(), compresslevel=9))
        if ok:
            return total, "built-file", None, None
    if ch["vis_gzip"] is not None:
        br = ch["vis_brotli"]
        return ch["vis_gzip"], "visualizer", br, ("visualizer" if br is not None else None)
    return None, None, None, None


def sum_known(vals):
    vals = list(vals)
    return sum(vals) if vals and all(v is not None for v in vals) else None


def basis_of(bases):
    s = sorted(set(x for x in bases if x))
    if not s or None in bases:
        return None
    return s[0] if len(s) == 1 else "mixed: " + ", ".join(s)


def find_chain(b, target, allow_dynamic):
    entries = b["entry_modules"]
    if target in entries:
        return [{"module": target}]
    prev = {target: None}
    q = deque([target])
    while q:
        cur = q.popleft()
        for src, kind, req in b["rev"].get(cur, []):
            if src in prev or (kind == "dynamic" and not allow_dynamic):
                continue
            prev[src] = (cur, kind, req)
            if src in entries:
                path = [{"module": src}]
                node = src
                while prev[node] is not None:
                    nxt, k, r = prev[node]
                    step = {"module": nxt, "via": k}
                    if r:
                        step["request"] = r
                    path.append(step)
                    node = nxt
                return path
            q.append(src)
    return None


def chain_for(b, target):
    c = find_chain(b, target, False)
    return c if c is not None else find_chain(b, target, True)


def analyze(b, dist=None, top=10, why=None):
    chunks = b["chunks"]
    for ch in chunks.values():
        ch["gzip"], ch["gzip_basis"], ch["brotli"], ch["brotli_basis"] = compress_chunk(b, ch, dist)
    initial_keys = set(k for e in b["entries"].values() for k in e["chunks"])
    mods = b["modules"]
    for m in mods.values():
        m["initial"] = any(c in initial_keys for c in m["chunks"])
        m["pkg"] = package_of(m["path"])
    res = {"format": b["format"], "tool": b["tool"], "raw_basis": b["raw_basis"],
           "module_basis": b["module_basis"], "notes": list(b["notes"]), "entries": [],
           "lazy_chunks": [], "largest_modules": [], "packages": [], "duplicates": [],
           "in_several_chunks": [], "flags": []}
    for name, e in b["entries"].items():
        cl = [chunks[k] for k in e["chunks"] if k in chunks]
        res["entries"].append({
            "name": name,
            "js_raw": sum(c["raw"] for c in cl),
            "gzip": sum_known(c["gzip"] for c in cl),
            "gzip_basis": basis_of([c["gzip_basis"] for c in cl]) if cl else None,
            "brotli": sum_known(c["brotli"] for c in cl),
            "brotli_basis": basis_of([c["brotli_basis"] for c in cl]) if cl else None,
            "css_raw": sum(c["css_raw"] for c in cl),
            "chunks": [{"key": c["key"], "files": c["files"], "raw": c["raw"], "gzip": c["gzip"],
                        "gzip_basis": c["gzip_basis"]} for c in cl],
        })
    res["entries"].sort(key=lambda e: -e["js_raw"])

    def chunk_contents(key, n=3):
        agg = defaultdict(int)
        for m in mods.values():
            if key in m["chunks"]:
                agg[owner_label(m["path"])] += m["chunk_sizes"].get(key, m["size"])
        return [{"owner": o, "size": s} for o, s in sorted(agg.items(), key=lambda kv: -kv[1])[:n]]

    for ch in sorted(chunks.values(), key=lambda c: -c["raw"]):
        if ch["key"] in initial_keys:
            continue
        res["lazy_chunks"].append({"key": ch["key"], "files": ch["files"], "raw": ch["raw"], "gzip": ch["gzip"],
                                   "gzip_basis": ch["gzip_basis"], "loaded_from": sorted(set(ch["loaded_from"])),
                                   "mostly": chunk_contents(ch["key"])})
    for m in sorted(mods.values(), key=lambda m: -m["size"])[:top]:
        res["largest_modules"].append({"path": m["path"], "package": m["pkg"][0] if m["pkg"] else None,
                                       "size": m["size"], "initial": m["initial"], "chunks": sorted(c for c in m["chunks"] if c)})
    pkgs = {}
    for m in mods.values():
        if not m["pkg"]:
            continue
        name, install, version = m["pkg"]
        p = pkgs.setdefault(name, {"name": name, "size": 0, "initial_size": 0, "lazy_size": 0, "modules": 0,
                                   "installs": {}, "cjs": False, "gzip": 0, "gzip_known": True})
        p["size"] += m["size"]
        if m.get("gzip") is None:
            p["gzip_known"] = False
        else:
            p["gzip"] += m["gzip"]
        p["modules"] += 1
        if m["initial"]:
            p["initial_size"] += m["size"]
        else:
            p["lazy_size"] += m["size"]
        p["cjs"] = p["cjs"] or m["cjs"]
        inst = p["installs"].setdefault(install, {"install": install, "version": version, "size": 0,
                                                  "initial_size": 0, "modules": []})
        inst["size"] += m["size"]
        if m["initial"]:
            inst["initial_size"] += m["size"]
        inst["modules"].append(m["path"])
    plist = sorted(pkgs.values(), key=lambda p: -p["size"])
    for p in plist:
        res["packages"].append({"name": p["name"], "size": p["size"], "initial_size": p["initial_size"],
                                "lazy_size": p["lazy_size"], "modules": p["modules"],
                                "installs": len(p["installs"]), "commonjs": p["cjs"],
                                "gzip": p["gzip"] if p["gzip_known"] else None})
    # duplicates
    for p in plist:
        if len(p["installs"]) < 2:
            continue
        dup = {"package": p["name"], "installs": []}
        for inst in sorted(p["installs"].values(), key=lambda i: -i["size"]):
            members = set(inst["modules"])
            pulled = []
            for mk in inst["modules"]:
                for src, kind, req in b["rev"].get(mk, []):
                    if src in members:
                        continue
                    label = owner_label(src)
                    item = "%s (%s)" % (label, req) if req else label
                    if item not in pulled:
                        pulled.append(item)
            first = None
            for mk in inst["modules"]:
                c = chain_for(b, mk)
                if c and (first is None or len(c) < len(first)):
                    first = c
            dup["installs"].append({"install": inst["install"], "version": inst["version"],
                                    "size": inst["size"], "initial_size": inst["initial_size"],
                                    "pulled_in_by": pulled, "chain": first})
        res["duplicates"].append(dup)
    # modules copied into several chunks
    several = defaultdict(lambda: {"size": 0, "extra": 0, "chunks": set(), "modules": 0})
    for m in mods.values():
        real = [c for c in m["chunks"] if c]
        if len(real) > 1:
            s = several[owner_label(m["path"])]
            s["size"] += m["size"]
            s["extra"] += m["size"] * (len(real) - 1)
            s["chunks"].update(real)
            s["modules"] += 1
    for owner, s in sorted(several.items(), key=lambda kv: -kv[1]["extra"]):
        if s["extra"] >= 1024:
            res["in_several_chunks"].append({"owner": owner, "size": s["size"], "extra_copies_size": s["extra"],
                                             "chunks": sorted(s["chunks"]), "modules": s["modules"]})
    # flags, per install path so two copies of one package are judged separately
    for p in plist:
        name = p["name"]
        several_installs = len(p["installs"]) > 1
        for inst in p["installs"].values():
            members = set(inst["modules"])
            label = inst["install"] if several_installs else name
            size = inst["size"]
            initial = inst["initial_size"] > 0
            cjs = any(mods[mk]["cjs"] for mk in members)
            prebuilt = all(".production.min." in mk or mk.endswith(".min.js") for mk in members)
            bare = []
            for mk in inst["modules"]:
                for src, kind, req in b["rev"].get(mk, []):
                    if src not in members and req == name:
                        lbl = owner_label(src)
                        if lbl not in bare:
                            bare.append(lbl)
            if bare and cjs and size >= 10 * KIB:
                res["flags"].append({"kind": "whole-library-commonjs", "package": label, "size": size, "initial": initial,
                                     "detail": "imported by its bare name \"%s\" from %s; this copy is CommonJS, so nothing in it is tree-shaken" % (name, ", ".join(bare))})
            elif bare and len(members) >= 20:
                res["flags"].append({"kind": "barrel-import", "package": label, "size": size, "initial": initial,
                                     "detail": "%d modules included through the bare import \"%s\" from %s; check whether it is shaken" % (len(members), name, ", ".join(bare))})
            elif cjs and inst["initial_size"] >= 10 * KIB and not prebuilt:
                res["flags"].append({"kind": "commonjs-in-initial", "package": label, "size": inst["initial_size"], "initial": True,
                                     "detail": "CommonJS, so it cannot be tree-shaken"})
            locale = [mk for mk in inst["modules"] if re.search(r"/(locale|locales|i18n)/", mk) or "with-locales" in mk]
            if len(locale) >= 5 or any("with-locales" in mk for mk in locale):
                res["flags"].append({"kind": "locales", "package": label, "size": sum(mods[mk]["size"] for mk in locale),
                                     "initial": any(mods[mk]["initial"] for mk in locale),
                                     "detail": "%d locale module(s) included: %s" % (len(locale), ", ".join(sorted(locale)[:3]))})
            if name in POLYFILL_PACKAGES or name.endswith("-polyfill"):
                feats = [mk for mk in inst["modules"] if "/modules/" in mk] or list(inst["modules"])
                sample = sorted(set(os.path.basename(mk).rsplit(".", 1)[0] for mk in feats))
                res["flags"].append({"kind": "polyfill", "package": label, "size": size, "initial": initial,
                                     "detail": "%d module(s) in total; features: %s%s" % (len(members), ", ".join(sample[:16]), ", ..." if len(sample) > 16 else "")})
    if why:
        res["why"] = [why_one(b, q) for q in why]
    return res


def why_one(b, query):
    mods = b["modules"]
    targets = []
    pk_installs = defaultdict(list)
    for mk, m in mods.items():
        p = package_of(mk)
        if p and p[0] == query:
            pk_installs[p[1]].append(mk)
    if pk_installs:
        for install, members in sorted(pk_installs.items()):
            best = None
            for mk in members:
                c = chain_for(b, mk)
                if c and (best is None or len(c) < len(best[1])):
                    best = (mk, c)
            targets.append({"install": install, "module": best[0] if best else members[0],
                            "chain": best[1] if best else None})
    else:
        hits = [mk for mk in mods if mk == query or mk.endswith("/" + query) or query in mk]
        hits.sort(key=lambda mk: (mk != query, -mods[mk]["size"]))
        for mk in hits[:3]:
            targets.append({"module": mk, "chain": chain_for(b, mk)})
    for t in targets:
        t["importers"] = sorted(set("%s (%s)" % (s, r) if r else s for s, k, r in b["rev"].get(t["module"], [])))[:8]
        t["initial"] = mods[t["module"]].get("initial", False)
    return {"query": query, "matches": targets}


# ---------------------------------------------------------------- budgets and compare

SIZE_RE = re.compile(r"^\s*([0-9]+(?:\.[0-9]+)?)\s*(b|kb|kib|mb|mib)?\s*$", re.I)
UNIT = {None: 1, "b": 1, "kb": 1000, "kib": 1024, "mb": 1000000, "mib": 1048576}


def parse_budgets(items):
    out = []
    for it in items or []:
        if "=" not in it:
            raise InputError("--budget takes ENTRY=SIZE, e.g. main=170000, main=170kB or main=gzip:60kB; got %r" % it)
        k, v = it.split("=", 1)
        kind = "raw"
        if v.lower().startswith("gzip:"):
            kind, v = "gzip", v[5:]
        m = SIZE_RE.match(v)
        if not m:
            raise InputError("--budget size must be bytes or a number with kB / KiB: %r" % it)
        out.append((k.strip(), kind, float(m.group(1)) * UNIT[(m.group(2) or "").lower() or None]))
    return out


def check_budgets(res, budgets):
    rows = []
    for key, kind, limit in budgets:
        for e in res["entries"]:
            if key in ("*", e["name"], stem(e["name"])):
                val = e["js_raw"] if kind == "raw" else e["gzip"]
                row = {"entry": e["name"], "kind": kind, "limit": int(limit), "value": val,
                       "basis": res["raw_basis"] if kind == "raw" else e["gzip_basis"],
                       "pass": None if val is None else val <= limit}
                if val is None:
                    row["note"] = "compressed size not measured; pass --dist with the built files"
                rows.append(row)
        if key != "*" and not any(r["entry"] == key or stem(r["entry"]) == key for r in rows):
            rows.append({"entry": key, "kind": kind, "limit": int(limit), "value": None, "basis": None, "pass": None,
                         "note": "no entry by this name"})
    return rows


def compare(b1, b2, r1, r2, top):
    out = {"before": {"tool": r1["tool"]}, "after": {"tool": r2["tool"]}, "entries": [], "chunks": [],
           "packages": [], "modules_added": [], "modules_removed": [], "modules_changed": [],
           "moved_to_initial": [], "moved_to_lazy": []}
    e1 = {e["name"]: e for e in r1["entries"]}
    e2 = {e["name"]: e for e in r2["entries"]}
    for name in list(e1) + [n for n in e2 if n not in e1]:
        a, c = e1.get(name), e2.get(name)
        out["entries"].append({"name": name, "raw_before": a["js_raw"] if a else 0, "raw_after": c["js_raw"] if c else 0,
                               "gzip_before": a["gzip"] if a else 0, "gzip_after": c["gzip"] if c else 0,
                               "gzip_basis": basis_of([x["gzip_basis"] for x in (a, c) if x])})
    for e in out["entries"]:
        e["raw_delta"] = e["raw_after"] - e["raw_before"]
        e["gzip_delta"] = (e["gzip_after"] - e["gzip_before"]
                           if e["gzip_after"] is not None and e["gzip_before"] is not None else None)
    for key in list(b1["chunks"]) + [k for k in b2["chunks"] if k not in b1["chunks"]]:
        a, c = b1["chunks"].get(key), b2["chunks"].get(key)
        d = (c["raw"] if c else 0) - (a["raw"] if a else 0)
        out["chunks"].append({"key": key, "initial_before": a["initial"] if a else None,
                              "initial_after": c["initial"] if c else None,
                              "raw_before": a["raw"] if a else 0, "raw_after": c["raw"] if c else 0, "raw_delta": d,
                              "loaded_from": sorted(set((c or a)["loaded_from"])),
                              "status": "added" if not a else "removed" if not c else "changed" if d else "same"})
    out["chunks"].sort(key=lambda x: -abs(x["raw_delta"]))
    out["chunks"] = [c for c in out["chunks"] if c["status"] != "same"]
    p1 = {p["name"]: p for p in r1["packages"]}
    p2 = {p["name"]: p for p in r2["packages"]}
    for name in set(p1) | set(p2):
        a, c = p1.get(name), p2.get(name)
        row = {"name": name, "size_before": a["size"] if a else 0, "size_after": c["size"] if c else 0,
               "initial_before": a["initial_size"] if a else 0, "initial_after": c["initial_size"] if c else 0,
               "status": "added" if not a else "removed" if not c else "changed"}
        row["delta"] = row["size_after"] - row["size_before"]
        row["initial_delta"] = row["initial_after"] - row["initial_before"]
        if row["delta"] or row["initial_delta"]:
            if c:
                mk = next((m for m in sorted(b2["modules"]) if (package_of(m) or ("",))[0] == name), None)
                row["chain_after"] = chain_for(b2, mk) if mk else None
            out["packages"].append(row)
        if a and c and a["initial_size"] == 0 and c["initial_size"] > 0:
            out["moved_to_initial"].append(name)
        if a and c and a["initial_size"] > 0 and c["initial_size"] == 0:
            out["moved_to_lazy"].append(name)
    out["packages"].sort(key=lambda x: (-abs(x["initial_delta"]), -abs(x["delta"])))
    m1, m2 = b1["modules"], b2["modules"]
    added = sorted((k for k in m2 if k not in m1), key=lambda k: -m2[k]["size"])
    for k in added[:top]:
        out["modules_added"].append({"path": k, "size": m2[k]["size"], "initial": m2[k]["initial"],
                                     "chain": chain_for(b2, k) if m2[k]["initial"] else None})
    out["modules_added_total"] = {"count": len(added), "size": sum(m2[k]["size"] for k in added),
                                  "initial_size": sum(m2[k]["size"] for k in added if m2[k]["initial"])}
    removed = sorted((k for k in m1 if k not in m2), key=lambda k: -m1[k]["size"])
    for k in removed[:top]:
        out["modules_removed"].append({"path": k, "size": m1[k]["size"], "initial_before": m1[k]["initial"]})
    changed = sorted((k for k in m1 if k in m2 and m1[k]["size"] != m2[k]["size"]),
                     key=lambda k: -abs(m2[k]["size"] - m1[k]["size"]))
    moved = [k for k in m1 if k in m2 and not m1[k]["initial"] and m2[k]["initial"]]
    out["modules_moved_to_initial"] = {"count": len(moved), "size": sum(m2[k]["size"] for k in moved),
                                       "modules": [{"path": k, "size": m2[k]["size"]} for k in
                                                   sorted(moved, key=lambda k: -m2[k]["size"])[:top]]}
    def totals(b):
        init = sum(c["raw"] for c in b["chunks"].values() if c["initial"])
        return init, sum(c["raw"] for c in b["chunks"].values()) - init
    i1, l1 = totals(b1)
    i2, l2 = totals(b2)
    out["totals"] = {"all_before": i1 + l1, "all_after": i2 + l2, "initial_before": i1, "initial_after": i2,
                     "lazy_before": l1, "lazy_after": l2}
    for k in changed[:top]:
        out["modules_changed"].append({"path": k, "size_before": m1[k]["size"], "size_after": m2[k]["size"],
                                       "initial_before": m1[k]["initial"], "initial_after": m2[k]["initial"]})
    return out


# ---------------------------------------------------------------- project files around the stats

# First browser version with the feature native (MDN browser-compat data). core-js can keep a
# polyfill a little longer to patch spec bugs, so a rebuild confirms the removal.
POLYFILL_FEATURES = {
    "es.promise": ("Promise", r"\bPromise\b", {"chrome": "67", "edge": "79", "firefox": "69", "safari": "11"}),
    "es.promise.all-settled": ("Promise.allSettled", r"\bPromise\.allSettled\b", {"chrome": "76", "edge": "79", "firefox": "71", "safari": "13"}),
    "es.promise.any": ("Promise.any", r"\bPromise\.any\b", {"chrome": "85", "edge": "85", "firefox": "79", "safari": "14"}),
    "es.promise.with-resolvers": ("Promise.withResolvers", r"\bPromise\.withResolvers\b", {"chrome": "119", "edge": "119", "firefox": "121", "safari": "17.4"}),
    "es.global-this": ("globalThis", r"\bglobalThis\b", {"chrome": "71", "edge": "79", "firefox": "65", "safari": "12.1"}),
    "es.array.flat": ("Array.prototype.flat", r"\.flat\(", {"chrome": "69", "edge": "79", "firefox": "62", "safari": "12"}),
    "es.array.flat-map": ("Array.prototype.flatMap", r"\.flatMap\(", {"chrome": "69", "edge": "79", "firefox": "62", "safari": "12"}),
    "es.array.includes": ("Array.prototype.includes", r"\.includes\(", {"chrome": "47", "edge": "14", "firefox": "43", "safari": "9"}),
    "es.array.at": ("Array.prototype.at", r"\.at\(", {"chrome": "92", "edge": "92", "firefox": "90", "safari": "15.4"}),
    "es.string.at-alternative": ("String.prototype.at", r"\.at\(", {"chrome": "92", "edge": "92", "firefox": "90", "safari": "15.4"}),
    "es.array.find-last": ("Array.prototype.findLast", r"\.findLast\(", {"chrome": "97", "edge": "97", "firefox": "104", "safari": "15.4"}),
    "es.array.find-last-index": ("Array.prototype.findLastIndex", r"\.findLastIndex\(", {"chrome": "97", "edge": "97", "firefox": "104", "safari": "15.4"}),
    "es.array.to-sorted": ("Array.prototype.toSorted", r"\.toSorted\(", {"chrome": "110", "edge": "110", "firefox": "115", "safari": "16"}),
    "es.array.to-reversed": ("Array.prototype.toReversed", r"\.toReversed\(", {"chrome": "110", "edge": "110", "firefox": "115", "safari": "16"}),
    "es.array.to-spliced": ("Array.prototype.toSpliced", r"\.toSpliced\(", {"chrome": "110", "edge": "110", "firefox": "115", "safari": "16"}),
    "es.array.with": ("Array.prototype.with", r"\.with\(", {"chrome": "110", "edge": "110", "firefox": "115", "safari": "16"}),
    "es.array.from-async": ("Array.fromAsync", r"\bArray\.fromAsync\b", {"chrome": "121", "edge": "121", "firefox": "115", "safari": "16.4"}),
    "es.object.from-entries": ("Object.fromEntries", r"\bObject\.fromEntries\b", {"chrome": "73", "edge": "79", "firefox": "63", "safari": "12.1"}),
    "es.object.has-own": ("Object.hasOwn", r"\bObject\.hasOwn\b", {"chrome": "93", "edge": "93", "firefox": "92", "safari": "15.4"}),
    "es.object.group-by": ("Object.groupBy", r"\bObject\.groupBy\b", {"chrome": "117", "edge": "117", "firefox": "119", "safari": "17.4"}),
    "es.map.group-by": ("Map.groupBy", r"\bMap\.groupBy\b", {"chrome": "117", "edge": "117", "firefox": "119", "safari": "17.4"}),
    "es.string.replace-all": ("String.prototype.replaceAll", r"\.replaceAll\(", {"chrome": "85", "edge": "85", "firefox": "77", "safari": "13.1"}),
    "es.string.is-well-formed": ("String.prototype.isWellFormed", r"\.isWellFormed\(", {"chrome": "111", "edge": "111", "firefox": "119", "safari": "16.4"}),
    "es.set.union.v2": ("Set.prototype.union and the other Set methods", r"\.(union|intersection|difference|symmetricDifference|isSubsetOf|isSupersetOf|isDisjointFrom)\(", {"chrome": "122", "edge": "122", "firefox": "127", "safari": "17"}),
    "es.symbol": ("Symbol", r"\bSymbol\b", {"chrome": "49", "edge": "15", "firefox": "51", "safari": "10"}),
    "es.array.iterator": ("Array iterators", r"\bfor\s*\(.+\bof\b|\.(entries|keys|values)\(", {"chrome": "66", "edge": "79", "firefox": "60", "safari": "15.4"}),
    "es.map": ("Map", r"\bnew\s+Map\b", {"chrome": "51", "edge": "15", "firefox": "53", "safari": "10"}),
    "es.set": ("Set", r"\bnew\s+Set\b", {"chrome": "51", "edge": "15", "firefox": "53", "safari": "10"}),
    "es.object.assign": ("Object.assign", r"\bObject\.assign\b", {"chrome": "49", "edge": "79", "firefox": "36", "safari": "9"}),
    "es.object.entries": ("Object.entries", r"\bObject\.entries\b", {"chrome": "54", "edge": "14", "firefox": "47", "safari": "10.1"}),
    "es.object.values": ("Object.values", r"\bObject\.values\b", {"chrome": "54", "edge": "14", "firefox": "47", "safari": "10.1"}),
    "es.promise.finally": ("Promise.prototype.finally", r"\.finally\(", {"chrome": "67", "edge": "79", "firefox": "69", "safari": "13.1"}),
    "es.string.pad-start": ("String.prototype.padStart", r"\.padStart\(", {"chrome": "57", "edge": "15", "firefox": "48", "safari": "15.4"}),
    "es.string.pad-end": ("String.prototype.padEnd", r"\.padEnd\(", {"chrome": "57", "edge": "15", "firefox": "48", "safari": "15.4"}),
    "es.string.includes": ("String.prototype.includes", r"\.includes\(", {"chrome": "51", "edge": "15", "firefox": "40", "safari": "10"}),
    "web.url": ("URL", r"\bnew\s+URL\b", {"chrome": "67", "edge": "79", "firefox": "57", "safari": "14.1"}),
    "web.url-search-params": ("URLSearchParams", r"\bURLSearchParams\b", {"chrome": "67", "edge": "79", "firefox": "57", "safari": "14.1"}),
    "web.structured-clone": ("structuredClone", r"\bstructuredClone\(", {"chrome": "98", "edge": "98", "firefox": "94", "safari": "15.4"}),
}
BROWSER_ALIAS = {"chrome": "chrome", "edge": "edge", "firefox": "firefox", "ff": "firefox", "safari": "safari",
                 "ios_saf": "safari", "ios": "safari"}
SKIP_DIRS = {"node_modules", ".git", "dist", "build", "out", "coverage", ".next", ".nuxt", ".svelte-kit", ".cache", ".turbo"}
SRC_EXT = (".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".vue", ".svelte")
CONFIG_RE = re.compile(r"^((webpack|vite|rollup|esbuild|rspack|rsbuild|tsup|next|nuxt|astro|svelte|craco|babel)\.config(\.[\w-]+)?\.[cm]?[jt]s"
                       r"|build\.[cm]?[jt]s|tsconfig(\.[\w-]+)?\.json|\.babelrc(\.json)?|\.size-limit(\.json|\.[cm]?js)?)$")
SPEC_RES = [("static", re.compile(r"""\bfrom\s*['"]([^'"]+)['"]""")),
            ("side-effect", re.compile(r"""(?m)^\s*import\s*['"]([^'"]+)['"]""")),
            ("dynamic", re.compile(r"""\bimport\s*\(\s*['"]([^'"]+)['"]\s*\)""")),
            ("require", re.compile(r"""\brequire\s*\(\s*['"]([^'"]+)['"]\s*\)"""))]
NS_RE = re.compile(r"""\bimport\s+\*\s+as\s+([\w$]+)\s+from\s*['"]([^'"]+)['"]""")


def ver_tuple(v):
    out = []
    for part in str(v).split("."):
        if not part.isdigit():
            break
        out.append(int(part))
    return tuple(out) or (0,)


def bare_package(spec):
    if not spec or spec.startswith((".", "/")) or ":" in spec.split("/")[0]:
        return None
    parts = spec.split("/")
    return "/".join(parts[:2]) if spec.startswith("@") and len(parts) > 1 else parts[0]


def read_text(path, limit=1000000):
    try:
        if os.path.getsize(path) > limit:
            return None
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return None


def read_json(path):
    t = read_text(path, 20000000)
    if t is None:
        return None
    try:
        return json.loads(t)
    except ValueError:
        return None


def find_root(stats_path, root):
    if root:
        return os.path.abspath(root)
    if not stats_path or stats_path == "-":
        return None
    d = os.path.dirname(os.path.abspath(stats_path))
    cands = [d, os.path.dirname(d), os.path.dirname(os.path.dirname(d))]
    for c in cands:
        if any(os.path.exists(os.path.join(c, f)) for f in ("package.json", ".browserslistrc")):
            return c
    for c in cands:
        if os.path.isdir(os.path.join(c, "src")):
            return c
    return d


def parse_browserslist(queries):
    """{browser: min version tuple} when every query is a plain version query, else None."""
    targets = {}
    for q in queries:
        q = q.strip().lower()
        if not q:
            continue
        m = re.fullmatch(r"([a-z_]+)\s*(>=|>)\s*([0-9.]+)", q) or re.fullmatch(r"([a-z_]+)\s+([0-9.]+)(?:\s*-\s*[0-9.]+)?", q)
        if not m or m.group(1) not in BROWSER_ALIAS:
            return None
        if len(m.groups()) == 3:
            v = ver_tuple(m.group(3))
            if m.group(2) == ">":
                v = v[:-1] + (v[-1] + 1,)
        else:
            v = ver_tuple(m.group(2))
        b = BROWSER_ALIAS[m.group(1)]
        targets[b] = min(targets.get(b, v), v)
    return targets or None


def browserslist_queries(raw):
    lines = []
    section = None
    prod = []
    for line in raw.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1].strip().lower()
            continue
        for q in line.split(","):
            (prod if section == "production" else lines if section is None else []).append(q.strip())
    return prod or lines


def build_targets(text):
    toks = []
    for m in re.finditer(r"""\btarget\s*:\s*(\[[^\]]*\]|['"][^'"]+['"])""", text):
        toks += re.findall(r"""['"]([^'"]+)['"]""", m.group(1))
    for m in re.finditer(r"""--target=([^\s'"]+)""", text):
        toks += m.group(1).split(",")
    out = []
    for t in toks:
        out += [x.strip() for x in t.split(",") if x.strip()]
    return out


def esbuild_style_targets(tokens):
    targets = {}
    for t in tokens:
        m = re.fullmatch(r"(chrome|edge|firefox|safari|ios)([0-9][0-9.]*)", t.lower())
        if m:
            b = BROWSER_ALIAS[m.group(1)]
            v = ver_tuple(m.group(2))
            targets[b] = min(targets.get(b, v), v)
    return targets or None


def lock_index(root):
    for name in ("package-lock.json", "npm-shrinkwrap.json"):
        data = read_json(os.path.join(root, name))
        if not isinstance(data, dict):
            continue
        pk = data.get("packages")
        if isinstance(pk, dict):
            return name, pk
        deps = data.get("dependencies")
        if isinstance(deps, dict):  # lockfile v1: nested dependencies
            flat = {}
            def walk(d, prefix):
                for n, info in d.items():
                    path = prefix + "node_modules/" + n
                    flat[path] = {"version": info.get("version"), "dependencies": info.get("requires") or {}}
                    if isinstance(info.get("dependencies"), dict):
                        walk(info["dependencies"], path + "/")
            walk(deps, "")
            return name, flat
    return None, None


def project_context(root, res, b):
    if not root or not os.path.isdir(root):
        return None
    ctx = {"root": root, "found": [], "absent": [], "browserslist": None, "build_targets": [], "ts_target": None,
           "targets": None, "targets_from": None, "budgets": [], "versions": {}, "lockfile": None,
           "dependents": {}, "sources_on_disk": [], "bundle_sources_absent": [], "importers": {}, "namespace": [],
           "polyfills": []}
    pkg = read_json(os.path.join(root, "package.json"))
    (ctx["found"] if isinstance(pkg, dict) else ctx["absent"]).append("package.json")
    queries, where = None, None
    rc = read_text(os.path.join(root, ".browserslistrc"))
    if rc is not None:
        ctx["found"].append(".browserslistrc")
        queries, where = browserslist_queries(rc), ".browserslistrc"
    else:
        ctx["absent"].append(".browserslistrc")
    if isinstance(pkg, dict):
        bl = pkg.get("browserslist")
        if isinstance(bl, dict):
            bl = bl.get("production") or bl.get("defaults")
        if isinstance(bl, str):
            bl = [bl]
        if isinstance(bl, list):
            if queries is None:
                queries, where = [str(x) for x in bl], "package.json browserslist"
            else:
                ctx["notes"] = ["package.json also has a browserslist field; browserslist refuses to run with both"]
        elif rc is None:
            ctx["absent"].append("package.json browserslist field")
        sl = pkg.get("size-limit") or pkg.get("bundlesize")
        if sl:
            ctx["budgets"].append("package.json %s: %s" % ("size-limit" if pkg.get("size-limit") else "bundlesize", json.dumps(sl)[:200]))
    if queries is not None:
        ctx["browserslist"] = {"from": where, "queries": queries}
    configs = []
    for d in (root, os.path.join(root, "config"), os.path.join(root, "scripts")):
        try:
            names = sorted(os.listdir(d))
        except OSError:
            continue
        for n in names:
            if CONFIG_RE.match(n) and os.path.isfile(os.path.join(d, n)):
                configs.append(os.path.relpath(os.path.join(d, n), root))
    if configs:
        ctx["found"] += configs
    else:
        ctx["absent"].append("bundler config (webpack/vite/rollup/esbuild config, build.mjs)")
    for rel in configs:
        text = read_text(os.path.join(root, rel)) or ""
        if rel.startswith("tsconfig") or "tsconfig" in rel:
            m = re.search(r'"target"\s*:\s*"([^"]+)"', text)
            if m:
                ctx["ts_target"] = {"from": rel, "target": m.group(1)}
            continue
        toks = build_targets(text)
        if toks:
            ctx["build_targets"].append({"from": rel, "target": toks})
        for key in ("maxEntrypointSize", "maxAssetSize", "hints"):
            for m in re.finditer(r"\b%s\s*:\s*([^,}\n]+)" % key, text):
                ctx["budgets"].append("%s %s: %s" % (rel, key, m.group(1).strip()))
        if os.path.basename(rel).startswith(".size-limit"):
            ctx["budgets"].append("%s: %s" % (rel, " ".join(text.split())[:200]))
    if queries is not None:
        ctx["targets"] = parse_browserslist(queries)
        ctx["targets_from"] = where if ctx["targets"] else None
    if ctx["targets"] is None and ctx["build_targets"]:
        toks = [t for bt in ctx["build_targets"] for t in bt["target"]]
        ctx["targets"] = esbuild_style_targets(toks)
        ctx["targets_from"] = ctx["build_targets"][0]["from"] + " target" if ctx["targets"] else None
    # versions: lockfile installed versions and declared ranges
    lname, lock = lock_index(root)
    if lname:
        ctx["found"].append(lname)
        ctx["lockfile"] = lname
    else:
        other = [n for n in ("yarn.lock", "pnpm-lock.yaml", "bun.lockb") if os.path.exists(os.path.join(root, n))]
        if other:
            ctx["found"] += other
            ctx["lockfile"] = other[0] + " (not parsed; read versions with yarn why / pnpm why)"
        else:
            ctx["absent"].append("lockfile")
    declared = {}
    if isinstance(pkg, dict):
        for sec in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
            for n, r in (pkg.get(sec) or {}).items():
                declared.setdefault(n, r)
    names = [p["name"] for p in res["packages"][:20]] + [d["package"] for d in res["duplicates"]]
    for n in dict.fromkeys(names):
        row = {"declared": declared.get(n)}
        if lock:
            row["installed"] = (lock.get("node_modules/" + n) or {}).get("version")
        ctx["versions"][n] = row
    for d in res["duplicates"]:
        for inst in d["installs"]:
            if lock and inst.get("version") is None:
                v = (lock.get(inst["install"]) or {}).get("version")
                if v:
                    inst["version"] = v
                    inst["version_from"] = lname
        if lock:
            wants = []
            if d["package"] in declared:
                wants.append("the app (package.json) %s" % declared[d["package"]])
            for path, info in sorted(lock.items()):
                if not path or not isinstance(info, dict):
                    continue
                r = (info.get("dependencies") or {}).get(d["package"]) or (info.get("peerDependencies") or {}).get(d["package"])
                if r:
                    owner = path.rsplit("node_modules/", 1)[-1]
                    wants.append("%s@%s %s" % (owner, info.get("version") or "?", r))
            ctx["dependents"][d["package"]] = wants
    # source files on disk
    files = []
    for dp, dns, fns in os.walk(root):
        dns[:] = [x for x in dns if x not in SKIP_DIRS and not x.startswith(".")]
        for fn in fns:
            if fn.endswith(SRC_EXT) and not CONFIG_RE.match(fn):
                files.append(os.path.relpath(os.path.join(dp, fn), root).replace("\\", "/"))
        if len(files) > 3000:
            break
    files.sort()
    ctx["sources_on_disk"] = files
    on_disk = set(files)
    bundle_src = sorted(m for m in b["modules"] if "node_modules/" not in m and m.endswith(SRC_EXT))
    ctx["bundle_sources_absent"] = [m for m in bundle_src if m not in on_disk]
    bundled = set(p["name"] for p in res["packages"])
    texts = {}
    for f in files:
        t = read_text(os.path.join(root, f))
        if t is None:
            continue
        texts[f] = t
        for kind, rx in SPEC_RES:
            for spec in rx.findall(t):
                pk = bare_package(spec)
                if pk in bundled:
                    ctx["importers"].setdefault(pk, [])
                    item = (f, kind, spec)
                    if item not in ctx["importers"][pk]:
                        ctx["importers"][pk].append(item)
        for ns, spec in NS_RE.findall(t):
            pk = bare_package(spec)
            if pk and re.search(r"\b%s\s*\[" % re.escape(ns), t):
                ctx["namespace"].append({"file": f, "package": pk, "name": ns})
    # polyfills against the targets
    for m in sorted(b["modules"]):
        pk = package_of(m)
        if not pk or pk[0] not in ("core-js", "core-js-pure") or "/modules/" not in m:
            continue
        feat = os.path.basename(m).rsplit(".", 1)[0]
        key = feat.replace("esnext.", "es.", 1)
        row = {"module": feat, "size": b["modules"][m]["size"], "imported_by": [], "used_in": []}
        for f, t in texts.items():
            if re.search(r"""['"]core-js(-pure)?/(modules|stable|actual|es|features)/%s['"]""" % re.escape(feat), t):
                row["imported_by"].append(f)
        info = POLYFILL_FEATURES.get(key)
        tg = ctx["targets"]
        if not info:
            row["verdict"] = "not in this script's table; check against the targets by hand"
        elif not tg:
            row["feature"] = info[0]
            row["verdict"] = "browser targets unknown"
        else:
            row["feature"] = info[0]
            short = []
            unknown = []
            for br, minv in sorted(tg.items()):
                nat = info[2].get(br)
                if nat is None:
                    unknown.append(br)
                elif minv < ver_tuple(nat):
                    short.append("%s %s < %s" % (br, ".".join(map(str, minv)), nat))
            if short:
                row["verdict"] = "NEEDED: native only from %s" % ", ".join(short)
                rx = re.compile(info[1])
                row["used_in"] = sorted(f for f, t in texts.items() if rx.search(t) and f not in row["imported_by"])
            elif unknown:
                row["verdict"] = "unknown for %s" % ", ".join(unknown)
            else:
                row["verdict"] = "not needed: native in every target (%s)" % ", ".join(
                    "%s %s" % (br, info[2][br]) for br in sorted(tg))
        ctx["polyfills"].append(row)
    return ctx


# ---------------------------------------------------------------- text output

def fmt_chain(chain):
    if not chain:
        return "(no chain from an entry found in the stats)"
    s = chain[0]["module"]
    for step in chain[1:]:
        arrow = " -import()-> " if step.get("via") == "dynamic" else " > "
        s += arrow + step["module"]
    return s


def gz_label(basis):
    return {"built-file": "measured from the built files, gzip -9", "visualizer": "from the visualizer's per-module figures"}.get(basis, basis or "not measured")


def comp_line(gzip_v, gzip_b, br_v=None, br_b=None):
    if gzip_v is None:
        return "compressed: not measured"
    s = "gzip %s [%s]" % (bkb(gzip_v), gz_label(gzip_b))
    if br_v is not None:
        s += ", brotli %s [%s]" % (bkb(br_v), gz_label(br_b))
    return s


def header(res):
    L = ["Bundle: %s. All sizes in bytes as the stats give them (kB = 1000 bytes)." % res["tool"],
         "Chunk sizes: %s." % res["raw_basis"],
         "Module and package sizes: %s." % res["module_basis"]]
    if not any(e["gzip"] is not None for e in res["entries"]):
        L.append("Compressed sizes: not measured; no built files were read (pass --dist DIR after a build).")
    for n in res["notes"]:
        L.append("Note: %s." % n)
    return L


def render_project(ctx):
    L = [""]
    if ctx is None:
        L.append("Project files: none read (stats from stdin and no --root)")
        return L
    rel = os.path.relpath(ctx["root"])
    L.append("Project files (root: %s)" % (rel if not rel.startswith("..") else ctx["root"]))
    L.append("  found: %s" % (", ".join(ctx["found"]) or "(none)"))
    L.append("  absent: %s" % (", ".join(ctx["absent"]) or "(none)"))
    for n in ctx.get("notes", []):
        L.append("  note: %s" % n)
    bl = ctx["browserslist"]
    if bl:
        L.append("  browserslist (%s): %s" % (bl["from"], ", ".join(bl["queries"])))
    for bt in ctx["build_targets"]:
        L.append("  build target (%s): %s" % (bt["from"], ", ".join(bt["target"])))
    if ctx["ts_target"]:
        L.append("  TypeScript target (%s): %s (syntax only; does not decide polyfills)" % (ctx["ts_target"]["from"], ctx["ts_target"]["target"]))
    if ctx["targets"]:
        L.append("  browser targets used for the polyfill check (%s): %s" % (
            ctx["targets_from"], ", ".join("%s >= %s" % (k, ".".join(map(str, v))) for k, v in sorted(ctx["targets"].items()))))
    elif bl:
        L.append("  browser targets: the queries are not plain version queries; resolve them with: npx --no browserslist")
    else:
        L.append("  browser targets: none found in the project files")
    L.append("  existing size budgets: %s" % ("; ".join(ctx["budgets"]) if ctx["budgets"] else "none found"))
    if ctx["lockfile"] and not ctx["lockfile"].endswith("not parsed; read versions with yarn why / pnpm why)"):
        vers = ["%s %s%s" % (n, v.get("installed") or "not in lockfile",
                             (" (declared %s)" % v["declared"]) if v.get("declared") else " (not a direct dependency)")
                for n, v in ctx["versions"].items()]
        if vers:
            L.append("  installed versions (%s; declared range from package.json): %s" % (ctx["lockfile"], "; ".join(vers)))
    else:
        vers = ["%s %s" % (n, v["declared"]) for n, v in ctx["versions"].items() if v.get("declared")]
        if vers:
            L.append("  declared ranges in package.json (installed versions unknown without a lockfile): %s" % "; ".join(vers))
    for pk, wants in ctx["dependents"].items():
        if wants:
            L.append("  who asks for %s: %s" % (pk, "; ".join(wants)))
    L.append("  source files on disk: %d%s" % (len(ctx["sources_on_disk"]),
             (": " + ", ".join(ctx["sources_on_disk"][:12]) + (" ..." if len(ctx["sources_on_disk"]) > 12 else "")) if ctx["sources_on_disk"] else ""))
    if ctx["bundle_sources_absent"]:
        a = ctx["bundle_sources_absent"]
        L.append("  bundled source files not on disk here (%d): %s%s" % (len(a), ", ".join(a[:10]), " ..." if len(a) > 10 else ""))
    for pk, imps in sorted(ctx["importers"].items()):
        per = {}
        for f, kind, spec in imps:
            per.setdefault(f, []).append((kind, spec))
        parts = []
        for f, items in per.items():
            if len(items) > 2:
                parts.append("%s (%d imports, e.g. '%s')" % (f, len(items), items[0][1]))
            else:
                parts.append("%s (%s)" % (f, ", ".join("%s '%s'" % it for it in items)))
        L.append("  %s imported in: %s" % (pk, "; ".join(parts[:8])))
    for n in ctx["namespace"]:
        L.append("  namespace import with a computed lookup: %s does import * as %s from '%s' and reads %s[...], so every export stays in the bundle"
                 % (n["file"], n["name"], n["package"], n["name"]))
    if ctx["polyfills"]:
        L.append("")
        L.append("Polyfills against the browser targets (first native version per MDN browser-compat data; a rebuild confirms each removal)")
        for p in ctx["polyfills"]:
            extra = ""
            if p["imported_by"]:
                extra += "; imported in %s" % ", ".join(p["imported_by"])
            if p["used_in"]:
                extra += "; feature used in %s" % ", ".join(p["used_in"])
            L.append("  %-28s %10s  %s%s%s" % (p["module"], kib(p["size"]), ("%s: " % p["feature"]) if p.get("feature") else "",
                                               p["verdict"], extra))
        removable = [p for p in ctx["polyfills"] if p["verdict"].startswith("not needed")]
        if removable:
            L.append("  not needed by the targets: %d module(s), %s in total" % (len(removable), kib(sum(p["size"] for p in removable))))
    return L


def render_budgets(rows, title):
    L = ["", title]
    for r in rows:
        if r["pass"] is None:
            L.append("  %s: budget %s %s; %s" % (r["entry"], r["kind"], kib(r["limit"]), r.get("note")))
        else:
            L.append("  %s: %s vs budget %s (%s) -> %s" % (r["entry"], kib(r["value"]), kib(r["limit"]), r["kind"],
                                                         "PASS" if r["pass"] else "OVER"))
    return L


def render_why(why):
    L = []
    for w in why or []:
        L.append("")
        L.append("Why is %s in the bundle?" % w["query"])
        if not w["matches"]:
            L.append("  no module or package by that name in the stats")
        for t in w["matches"]:
            head = t.get("install") or t["module"]
            L.append("  %s (%s)" % (head, "initial" if t["initial"] else "lazy"))
            L.append("    chain: %s" % fmt_chain(t["chain"]))
            if t["importers"]:
                L.append("    imported by: %s" % ", ".join(t["importers"]))
    return L


def render_single(res, budgets_rows):
    L = header(res)
    L.append("")
    L.append("Initial JS per entry (loaded before first render)")
    if not res["entries"]:
        L.append("  (no entries found)")
    for e in res["entries"]:
        L.append("  %s: %s%s%s" % (e["name"], bkb(e["js_raw"]),
                                   ("; " + comp_line(e["gzip"], e["gzip_basis"], e["brotli"], e["brotli_basis"])) if e["gzip"] is not None else "",
                                   ("; CSS %s" % kib(e["css_raw"])) if e["css_raw"] else ""))
        for c in e["chunks"]:
            L.append("    %-28s %14s  %s" % (c["key"], kib(c["raw"]), ", ".join(c["files"])))
    L.append("")
    L.append("Lazy chunks (loaded on demand, not on first render)")
    if not res["lazy_chunks"]:
        L.append("  (none)")
    for c in res["lazy_chunks"]:
        mostly = ", ".join("%s %s" % (x["owner"], kib(x["size"])) for x in c["mostly"])
        frm = ("; loaded from " + ", ".join(c["loaded_from"])) if c["loaded_from"] else ""
        L.append("  %s: %s%s; files %s%s; largest: %s" % (c["key"], kib(c["raw"]),
                 (", gzip %s" % kib(c["gzip"])) if c["gzip"] is not None else "", ", ".join(c["files"]), frm, mostly))
    L.append("")
    L.append("Largest modules (%s)" % res["module_basis"])
    for m in res["largest_modules"]:
        L.append("  %14s  %-8s %s  [%s]" % (kib(m["size"]), "initial" if m["initial"] else "lazy", m["path"], ", ".join(m["chunks"])))
    L.append("")
    L.append("Packages by size")
    for p in res["packages"][:15]:
        where = "initial %s" % kib(p["initial_size"]) if p["initial_size"] else "lazy only"
        if p["initial_size"] and p["lazy_size"]:
            where += ", lazy %s" % kib(p["lazy_size"])
        extra = []
        if p["installs"] > 1:
            extra.append("%d install paths" % p["installs"])
        if p["commonjs"]:
            extra.append("CommonJS")
        if p.get("gzip") is not None:
            extra.insert(0, "%s gzip [visualizer]" % kib(p["gzip"]))
        L.append("  %14s  %-28s %s; %d module(s)%s" % (kib(p["size"]), p["name"], where, p["modules"],
                                                     ("; " + ", ".join(extra)) if extra else ""))
    L.append("")
    L.append("Packages installed at more than one path")
    if not res["duplicates"]:
        L.append("  (none)")
    for d in res["duplicates"]:
        L.append("  %s: %d copies" % (d["package"], len(d["installs"])))
        for i in d["installs"]:
            ver = i["version"] or "version not in stats or lockfile (read it with npm ls %s)" % d["package"]
            if i.get("version_from"):
                ver = "%s (from %s)" % (i["version"], i["version_from"])
            L.append("    %s  %s  %s (%s)" % (i["install"], ver, kib(i["size"]), "initial" if i["initial_size"] else "lazy"))
            L.append("      pulled in by: %s" % (", ".join(i["pulled_in_by"]) or "(no importer in stats)"))
            L.append("      chain: %s" % fmt_chain(i["chain"]))
    if res["in_several_chunks"]:
        L.append("")
        L.append("Modules copied into more than one chunk")
        for s in res["in_several_chunks"]:
            L.append("  %s: %d module(s), %s each copy, %s extra, in %s" % (s["owner"], s["modules"], kib(s["size"]),
                                                                       kib(s["extra_copies_size"]), ", ".join(s["chunks"])))
    L.append("")
    L.append("Flags")
    if not res["flags"]:
        L.append("  (none)")
    for f in res["flags"]:
        L.append("  %s: %s, %s, %s; %s" % (f["kind"], f["package"], kib(f["size"]), "initial" if f["initial"] else "lazy", f["detail"]))
    L.extend(render_project(res.get("project")))
    if budgets_rows:
        L.extend(render_budgets(budgets_rows, "Budgets on each entry's initial JS"))
    L.extend(render_why(res.get("why")))
    return "\n".join(L) + "\n"


def signed(n):
    if n is None:
        return "n/a"
    return ("+" if n > 0 else "") + kib(n)


def render_compare(cmp_, r1, r2, budgets_before, budgets_after):
    L = ["Before: %s. After: %s." % (cmp_["before"]["tool"], cmp_["after"]["tool"])] + header(r2)[1:] + [""]
    t = cmp_["totals"]
    L.append("All JS chunks: %s -> %s (%s); initial %s, lazy %s" % (
        bkb(t["all_before"]), bkb(t["all_after"]), signed(t["all_after"] - t["all_before"]),
        signed(t["initial_after"] - t["initial_before"]), signed(t["lazy_after"] - t["lazy_before"])))
    L.append("")
    L.append("Initial JS per entry")
    for e in cmp_["entries"]:
        gz = ""
        if e["gzip_before"] is not None and e["gzip_after"] is not None:
            gz = "; gzip %s -> %s (%s) [%s]" % (kib(e["gzip_before"]), kib(e["gzip_after"]), signed(e["gzip_delta"]), gz_label(e["gzip_basis"]))
        L.append("  %s: %s -> %s (%s)%s" % (e["name"], bkb(e["raw_before"]), bkb(e["raw_after"]), signed(e["raw_delta"]), gz))
    L.append("")
    L.append("Chunks that changed")
    for c in cmp_["chunks"][:15]:
        kind = "initial" if (c["initial_after"] if c["initial_after"] is not None else c["initial_before"]) else "lazy"
        if c["initial_before"] is not None and c["initial_after"] is not None and c["initial_before"] != c["initial_after"]:
            kind = "lazy -> initial" if c["initial_after"] else "initial -> lazy"
        L.append("  %-30s %-15s %12s -> %12s (%s) %s%s" % (c["key"], kind, kib(c["raw_before"]), kib(c["raw_after"]),
                                                         signed(c["raw_delta"]), c["status"],
                                                         ("; loaded with import() from " + ", ".join(c["loaded_from"])) if c["loaded_from"] and kind != "initial" else ""))
    L.append("")
    L.append("Packages that changed (sorted by change in initial size)")
    for p in cmp_["packages"][:15]:
        L.append("  %-28s total %s -> %s (%s); initial %s -> %s (%s) %s" % (
            p["name"], kib(p["size_before"]), kib(p["size_after"]), signed(p["delta"]),
            kib(p["initial_before"]), kib(p["initial_after"]), signed(p["initial_delta"]), p["status"]))
        if p.get("chain_after") and p["initial_delta"] > 0:
            L.append("      chain: %s" % fmt_chain(p["chain_after"]))
    if cmp_["moved_to_initial"]:
        L.append("  moved from lazy to initial: %s" % ", ".join(cmp_["moved_to_initial"]))
    if cmp_["moved_to_lazy"]:
        L.append("  moved from initial to lazy: %s" % ", ".join(cmp_["moved_to_lazy"]))
    t = cmp_["modules_added_total"]
    L.append("")
    L.append("Modules added: %d, %s, of which %s in initial chunks" % (t["count"], kib(t["size"]), kib(t["initial_size"])))
    for m in cmp_["modules_added"]:
        L.append("  %12s  %-8s %s" % (kib(m["size"]), "initial" if m["initial"] else "lazy", m["path"]))
        if m["chain"]:
            L.append("      chain: %s" % fmt_chain(m["chain"]))
    mv = cmp_["modules_moved_to_initial"]
    if mv["count"]:
        L.append("Modules moved from lazy to initial chunks: %d, %s" % (mv["count"], kib(mv["size"])))
        for m in mv["modules"]:
            L.append("  %12s  %s" % (kib(m["size"]), m["path"]))
    if cmp_["modules_changed"]:
        L.append("Modules that changed size")
        for m in cmp_["modules_changed"]:
            mvs = ""
            if m["initial_before"] != m["initial_after"]:
                mvs = " lazy -> initial" if m["initial_after"] else " initial -> lazy"
            L.append("  %s: %s -> %s%s" % (m["path"], kib(m["size_before"]), kib(m["size_after"]), mvs))
    if cmp_["modules_removed"]:
        L.append("Modules removed")
        for m in cmp_["modules_removed"]:
            L.append("  %12s  %s" % (kib(m["size"]), m["path"]))
    L.extend(render_project(r2.get("project")))
    if budgets_after:
        bmap = {(r["entry"], r["kind"], r["limit"]): r for r in budgets_before}
        L += ["", "Budgets on each entry's initial JS, before -> after"]
        for r in budgets_after:
            rb = bmap.get((r["entry"], r["kind"], r["limit"]))
            if r["pass"] is None:
                L.append("  %s: budget %s %s; %s" % (r["entry"], r["kind"], kib(r["limit"]), r.get("note")))
                continue
            L.append("  %s: budget %s (%s); before %s (%s), after %s (%s)" % (
                r["entry"], kib(r["limit"]), r["kind"], kib(rb["value"]) if rb else "n/a",
                ("PASS" if rb["pass"] else "OVER") if rb and rb["pass"] is not None else "n/a",
                kib(r["value"]), "PASS" if r["pass"] else "OVER"))
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------- main

def to_jsonable(o):
    if isinstance(o, (set, tuple)):
        return sorted(o) if isinstance(o, set) else list(o)
    raise TypeError(type(o))


def _main(argv=None):
    ap = argparse.ArgumentParser(description="Size a JS bundle from webpack stats, an esbuild metafile or rollup-plugin-visualizer raw data, and read the project files around it.")
    ap.add_argument("stats", nargs="?", help="stats file, or - for stdin")
    ap.add_argument("--compare", nargs=2, metavar=("BEFORE", "AFTER"), help="diff two stats files")
    ap.add_argument("--why", action="append", metavar="MODULE_OR_PACKAGE", help="print the import chain from an entry (repeatable)")
    ap.add_argument("--budget", action="append", metavar="ENTRY=SIZE",
                    help="budget on an entry's initial JS: bytes or kB/KiB (main=170kB), or gzip:SIZE when measured; * for every entry (repeatable)")
    ap.add_argument("--dist", metavar="DIR", help="build output folder; gzip the real emitted files when found")
    ap.add_argument("--root", metavar="DIR", help="project folder to read package.json, .browserslistrc, lockfile, configs and sources from (default: found next to the stats file)")
    ap.add_argument("--top", type=int, default=10, help="rows in the largest-module lists (default 10)")
    ap.add_argument("--json", action="store_true", help="print JSON instead of text")
    ap.add_argument("-o", "--output", metavar="PATH", help="write the report to PATH instead of stdout")
    args = ap.parse_args(argv)
    try:
        budgets = parse_budgets(args.budget)
        over = False
        if args.compare:
            if args.stats:
                raise InputError("give either one stats file or --compare BEFORE AFTER, not both")
            b1, b2 = load(args.compare[0]), load(args.compare[1])
            r1 = analyze(b1, None, args.top)
            r2 = analyze(b2, args.dist, args.top, args.why)
            r2["project"] = project_context(find_root(args.compare[1], args.root), r2, b2)
            cmp_ = compare(b1, b2, r1, r2, args.top)
            bb, ba = check_budgets(r1, budgets), check_budgets(r2, budgets)
            over = any(r["pass"] is False for r in ba)
            if args.json:
                payload = {"compare": cmp_, "budgets_before": bb, "budgets_after": ba, "why": r2.get("why"),
                           "project": r2["project"]}
                text = json.dumps(payload, indent=2, default=to_jsonable) + "\n"
            else:
                text = render_compare(cmp_, r1, r2, bb, ba)
                if r2.get("why"):
                    text += "\n".join(render_why(r2["why"])) + "\n"
        else:
            if not args.stats:
                raise InputError("give a stats file path, - for stdin, or --compare BEFORE AFTER")
            b = load(args.stats)
            res = analyze(b, args.dist, args.top, args.why)
            res["project"] = project_context(find_root(args.stats, args.root), res, b)
            rows = check_budgets(res, budgets)
            res["budgets"] = rows
            over = any(r["pass"] is False for r in rows)
            text = json.dumps(res, indent=2, default=to_jsonable) + "\n" if args.json else render_single(res, rows)
    except InputError as e:
        sys.stderr.write("bundle_stats: %s\n" % e)
        return 2
    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(text)
    else:
        sys.stdout.write(text)
    return 1 if over else 0



def main(argv=None):
    """Run, and turn an input that parses but has the wrong shape into one clear error."""
    try:
        return _main(argv)
    except (KeyError, TypeError, AttributeError, IndexError, ValueError) as e:
        print("error: couldn't read the input as webpack, esbuild or Vite stats (%s: %s). If it is one, this is a bug: "
              "please report it with the file." % (type(e).__name__, e), file=sys.stderr)
        return 2

if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""agent_config_scan.py - list what a coding agent's configuration actually grants.

Reads the agent config files found in the paths given (Claude Code settings at every scope,
.mcp.json, subagent files, Cursor, Codex, VS Code), merges Claude Code's scopes the way the
tool does, and prints the effective result plus the mechanical patterns a reviewer grades:
wide allow rules, a deny list an allowed interpreter walks around, hooks and other settings
that run shell, unpinned MCP packages, literal secrets (masked), subagents with no tool list.
It judges nothing; the reviewer does.

Usage:
  python3 agent_config_scan.py PATH [PATH ...] [--user HOME_DIR] [--managed FILE]
                               [--also FILE ...] [--json] [-o OUT]

  PATH       a project folder (searched for known config files) or one config file
  --user     a home folder: reads its .claude/settings.json, .claude.json, .claude/agents,
             .codex/config.toml and .cursor/mcp.json as user scope
  --managed  a managed-settings.json (organisation policy; outranks every other scope)
  --also     any other file a config references (an env file, a token file): it is
             searched for literal secrets and checked against .gitignore
  -o OUT     write the report to OUT instead of stdout

Stdlib only, Python 3.9+. Reads only the paths given; writes only OUT. No network.
"""
import argparse
import fnmatch
import hashlib
import json
import os
import re
import sys

try:
    import tomllib  # Python 3.11+
except ImportError:  # pragma: no cover
    tomllib = None

SCOPES = ["user", "project", "local", "managed"]  # low -> high precedence

# --- what an allow rule really lets run -------------------------------------------------
CODE_RUNNERS = {
    "python": "runs any code (`python -c`)", "python3": "runs any code (`python3 -c`)",
    "node": "runs any code (`node -e`)", "deno": "runs any code", "bun": "runs any code",
    "ruby": "runs any code (`ruby -e`)", "perl": "runs any code (`perl -e`)", "php": "runs any code",
    "bash": "runs any shell", "sh": "runs any shell", "zsh": "runs any shell",
    "pwsh": "runs any shell", "powershell": "runs any shell",
    "npm": "runs any package.json script, and `npm exec` downloads and runs any package",
    "pnpm": "runs any package.json script and `pnpm dlx` any package",
    "yarn": "runs any package.json script and `yarn dlx` any package",
    "npx": "downloads and runs any package", "bunx": "downloads and runs any package",
    "uvx": "downloads and runs any package", "pipx": "downloads and runs any package",
    "uv": "`uv run` runs any code", "pip": "installs packages whose setup code runs",
    "pip3": "installs packages whose setup code runs",
    "make": "runs whatever the Makefile says, and `make -f` any file",
    "just": "runs whatever the justfile says", "cargo": "`cargo run` and build scripts run any code",
    "go": "`go run` runs any code", "docker": "starts containers that can mount the host disk",
    "podman": "starts containers that can mount the host disk",
    "kubectl": "runs commands in the cluster the kubeconfig reaches",
    "git": "`git -c core.sshCommand=...`, aliases and hooks run commands; `git push` sends code out",
    "gh": "`gh api` makes any call the token allows, deletes included",
    "curl": "sends any file to any host, or downloads code", "wget": "sends data out or downloads code",
    "ssh": "runs commands on other machines", "scp": "copies files off the machine",
    "rsync": "copies files off the machine", "find": "`-exec` runs any command",
    "xargs": "runs whatever command follows", "env": "runs whatever command follows",
    "sudo": "runs any command as root", "eval": "runs any command", "exec": "runs any command",
    "nohup": "runs whatever command follows", "timeout": "runs whatever command follows",
    "watch": "runs whatever command follows", "awk": "`system()` runs commands",
    "sed": "GNU sed's `e` command runs commands", "rm": "deletes anything the user can",
}
OPEN_SUBCOMMANDS = {"npm run", "npm exec", "npm x", "pnpm run", "pnpm exec", "pnpm dlx", "yarn run", "yarn dlx",
                    "docker run", "docker compose", "docker exec", "podman run", "uv run", "uv tool", "poetry run",
                    "python -m", "python3 -m", "git config", "git -c", "go run", "cargo run", "gh api", "kubectl exec",
                    "make -f", "bash -c", "sh -c"}
WIDE_TOOLS = {
    "Bash": "any shell command without asking",
    "Edit": "edits any file without asking, the agent's own settings and hooks included",
    "Write": "writes any file without asking, the agent's own settings and hooks included",
    "MultiEdit": "edits any file without asking",
    "WebFetch": "fetches any URL without asking; a URL can carry data out in its query string",
    "WebSearch": "searches without asking; a query can carry data out",
}
RISKY_DOMAINS = ("raw.githubusercontent.com", "gist.githubusercontent.com", "githubusercontent.com",
                 "pastebin.com", "ngrok", "webhook.site", "requestbin", "transfer.sh", "s3.amazonaws.com")
SHELL_KEYS = ("statusLine", "apiKeyHelper", "awsAuthRefresh", "awsCredentialExport",
              "otelHeadersHelper", "fileSuggestion")
LAUNCH_FLAGS = ("dangerously-skip-permissions", "bypassPermissions", "dangerously-bypass-approvals-and-sandbox",
                "--yolo", "--full-auto", "danger-full-access", "--permission-mode")

FETCH_WORD = re.compile(r"\b(curl|wget|iwr|Invoke-WebRequest|Invoke-RestMethod)\b|https?://", re.I)
PIPE_TO_SHELL = re.compile(r"\|\s*(sudo\s+)?(ba|z|da|fi)?sh\b|\|\s*(python3?|node|iex)\b", re.I)
RUN_DOWNLOADED = re.compile(r"\b(bash|sh|zsh|source|python3?|node)\s+[^|;&]*(/tmp/|\$\(|<\()", re.I)

SECRET_PATTERNS = [
    re.compile(r"\b(ghp|gho|ghs|ghu|ghr)_[A-Za-z0-9]{12,}"), re.compile(r"\bgithub_pat_[A-Za-z0-9_]{12,}"),
    re.compile(r"\bglpat-[A-Za-z0-9_-]{8,}"), re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{8,}"),
    re.compile(r"\bsk-(ant-|proj-)?[A-Za-z0-9_-]{12,}"), re.compile(r"\b(sk|rk)_(live|test)_[A-Za-z0-9]{8,}"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"), re.compile(r"\bAIza[0-9A-Za-z_-]{20,}"),
    re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{12,}"), re.compile(r"://[^/\s:@\"']+:[^@\s\"'$]{3,}@"),
]
SECRET_NAME = re.compile(r"(TOKEN|SECRET|PASSWORD|PASSWD|API_?KEY|PRIVATE_?KEY|_PAT\b|^PAT$|AUTH|CREDENTIAL|DATABASE_URL|_DSN\b)", re.I)
REFERENCE = re.compile(r"^\s*(\$\{[^}]+\}|\$[A-Z_][A-Z0-9_]*|\{env:[^}]+\}|\$\{input:[^}]+\}|<[^>]+>)?\s*$")
REF_ANYWHERE = re.compile(r"\$\{[^}]+\}|\$[A-Z_][A-Z0-9_]*|\{env:[^}]+\}")
HIDDEN_CHARS = re.compile("[​-‏‪-‮⁠-⁤⁦-⁩﻿\U000e0000-\U000e007f]")


def read_text(path):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read()
    except (OSError, UnicodeDecodeError):
        return None


def strip_jsonc(text):
    """Remove // and /* */ comments and trailing commas, leaving strings intact."""
    out, i, n, in_str = [], 0, len(text), False
    while i < n:
        c = text[i]
        if in_str:
            out.append(c)
            if c == "\\" and i + 1 < n:
                out.append(text[i + 1]); i += 2; continue
            if c == '"':
                in_str = False
            i += 1; continue
        if c == '"':
            in_str = True; out.append(c); i += 1; continue
        if text.startswith("//", i):
            while i < n and text[i] != "\n":
                i += 1
            continue
        if text.startswith("/*", i):
            j = text.find("*/", i + 2)
            seg = text[i:(j + 2 if j >= 0 else n)]
            out.append("\n" * seg.count("\n"))
            i = j + 2 if j >= 0 else n; continue
        out.append(c); i += 1
    return re.sub(r",(\s*[}\]])", r"\1", "".join(out))


def load_json(path, notes):
    text = read_text(path)
    if text is None:
        return None, []
    try:
        return json.loads(strip_jsonc(text)), text.splitlines()
    except ValueError as e:
        notes.append("{}: not valid JSON ({}); skipped".format(path, e))
        return None, text.splitlines()


def mini_toml(text):
    """Enough TOML for agent configs: tables, dotted/quoted keys, strings, bools, numbers,
    arrays and inline tables. Used only when tomllib is unavailable (Python < 3.11)."""
    root, cur = {}, None
    cur = root

    def parse_value(s):
        s = s.strip()
        if s.startswith('"""') or s.startswith("'''"):
            return s[3:-3]
        if s.startswith('"'):
            return json.loads(s[: s.rfind('"') + 1])
        if s.startswith("'"):
            return s[1: s.rfind("'")]
        if s in ("true", "false"):
            return s == "true"
        if s.startswith("["):
            inner = s[1: s.rfind("]")]
            return [parse_value(p) for p in split_top(inner) if p.strip()]
        if s.startswith("{"):
            d = {}
            for p in split_top(s[1: s.rfind("}")]):
                if "=" in p:
                    k, v = p.split("=", 1)
                    d[unquote(k)] = parse_value(v)
            return d
        try:
            return int(s)
        except ValueError:
            try:
                return float(s)
            except ValueError:
                return s

    def split_top(s):
        parts, depth, buf, q = [], 0, "", None
        for ch in s:
            if q:
                buf += ch
                if ch == q:
                    q = None
                continue
            if ch in "\"'":
                q = ch
            elif ch in "[{":
                depth += 1
            elif ch in "]}":
                depth -= 1
            elif ch == "," and depth == 0:
                parts.append(buf); buf = ""; continue
            buf += ch
        parts.append(buf)
        return parts

    def unquote(k):
        k = k.strip()
        return k[1:-1] if len(k) > 1 and k[0] in "\"'" and k[-1] == k[0] else k

    def keypath(k):
        return [unquote(p) for p in re.findall(r'"[^"]*"|\'[^\']*\'|[^.]+', k.strip())]

    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        i += 1
        if not line or line.startswith("#"):
            continue
        m = re.match(r"^\[\[?([^\]]+)\]\]?\s*(#.*)?$", line)
        if m:
            cur = root
            for p in keypath(m.group(1)):
                cur = cur.setdefault(p, {})
            continue
        if "=" in line:
            k, v = line.split("=", 1)
            v = re.sub(r"\s+#[^\"']*$", "", v)
            while v.count("[") > v.count("]") and i < len(lines):  # multi-line array
                v += " " + re.sub(r"\s+#.*$", "", lines[i].strip()); i += 1
            ks = keypath(k)
            tgt = cur
            for p in ks[:-1]:
                tgt = tgt.setdefault(p, {})
            tgt[ks[-1]] = parse_value(v)
    return root


def load_toml(path, notes):
    text = read_text(path)
    if text is None:
        return None, []
    try:
        data = tomllib.loads(text) if tomllib else mini_toml(text)
    except Exception as e:  # noqa: BLE001 - report and continue
        notes.append("{}: not valid TOML ({}); skipped".format(path, e))
        return None, text.splitlines()
    return data, text.splitlines()


def line_of(lines, *needles):
    for i, ln in enumerate(lines or [], 1):
        if all(n in ln for n in needles):
            return i
    return 0


# Public token prefixes. Only these constant labels are printed, never characters of the secret.
TOKEN_KINDS = [("ghp_", "GitHub token"), ("github_pat_", "GitHub token"), ("gho_", "GitHub token"),
               ("sk-ant-", "Anthropic key"), ("sk-", "API key (sk-)"), ("xox", "Slack token"),
               ("AKIA", "AWS access key"), ("AIza", "Google API key"), ("glpat-", "GitLab token")]


def mask(value):
    """A secret as its kind, length and a short fingerprint, so two findings can be told apart
    or matched without printing any part of the value."""
    v = str(value)
    kind = next((label for pre, label in TOKEN_KINDS if v.startswith(pre)), "secret")
    return "[{}, {} chars, sha256:{}]".format(kind, len(v), hashlib.sha256(v.encode("utf-8")).hexdigest()[:8])


URL_CREDS = re.compile(r"(://[^/\s:@\"']+:)([^@\s\"'$]{3,})(@)")


def redact(text):
    """Mask every secret-shaped string in output; a URL keeps its user and host, loses its password."""
    text = URL_CREDS.sub(lambda m: m.group(1) + "****" + m.group(3), text)
    for p in SECRET_PATTERNS[:-1]:
        text = p.sub(lambda m: mask(m.group(0)), text)
    return text


def secret_in(value):
    if not isinstance(value, str):
        return False
    return any(p.search(value) for p in SECRET_PATTERNS)


def literal_secret(name, value):
    """A value written into the file (not a ${VAR} reference) that is a secret by shape or name."""
    if not isinstance(value, str) or not value.strip() or REFERENCE.match(value):
        return False
    if secret_in(value):
        return True
    rest = REF_ANYWHERE.sub("", value)
    rest = re.sub(r"^\s*(Bearer|Basic|Token|token)\b", "", rest).strip()
    return bool(rest) and bool(SECRET_NAME.search(name or ""))


class Report:
    def __init__(self):
        self.files, self.notes, self.flags, self.secrets = [], [], [], []
        self.claude = {}
        self.mcp, self.agents, self.codex, self.cursor_rules, self.vscode, self.launch = [], [], [], [], [], []

    def flag(self, kind, where, text, effect):
        self.flags.append({"kind": kind, "where": where, "text": text, "effect": effect})

    def secret(self, where, name, value, rel):
        self.secrets.append({"where": where, "name": name, "masked": mask(value), "file": rel})


def rel(path, base):
    try:
        r = os.path.relpath(path, base)
        return path if r.startswith("..") else r
    except ValueError:
        return path


def first_word(rule_body):
    body = rule_body.strip()
    return re.split(r"[\s:*]", body, 1)[0] if body else ""


def classify_rule(rule):
    """Return (wide?, effect) for one permission rule string."""
    if rule.strip().startswith("mcp__"):
        parts = rule.strip().split("__")
        if len(parts) == 2 or (len(parts) == 3 and parts[2] in ("*", "")):
            return True, "every tool on MCP server `{}`, writes included, without asking".format(parts[1])
        return False, ""
    m = re.match(r"^([A-Za-z_]+)(?:\((.*)\))?$", rule.strip())
    if not m:
        return False, ""
    tool, body = m.group(1), m.group(2)
    if body is None or body.strip() in ("*", "**", ":*", "*:*"):
        if tool in WIDE_TOOLS:
            return True, WIDE_TOOLS[tool]
        return False, ""
    if tool == "Bash":
        w = first_word(body)
        rest = body.strip()[len(w):].strip()
        sub = re.sub(r"\s*:?\*$", "", rest).strip()
        if w in CODE_RUNNERS and rest != sub and (not sub or "{} {}".format(w, sub) in OPEN_SUBCOMMANDS):
            return True, CODE_RUNNERS[w] if not sub else "`{} {}` with any arguments runs any code".format(w, sub)
        if w in CODE_RUNNERS and rest == "":
            return True, CODE_RUNNERS[w] + " (bare command; check whether arguments are matched)"
    if tool in ("Edit", "Write", "Read") and body.strip() in ("/**", "//**", "~/**", "**/*"):
        return True, "{} on every path".format(tool)
    if tool == "WebFetch" and "*" in body:
        return True, "fetches matching hosts without asking: " + body
    return False, ""


def scan_claude_settings(data, lines, scope, relpath, rep):
    if not isinstance(data, dict):
        return
    entry = {"scope": scope, "file": relpath, "data": data, "lines": lines}
    rep.claude.setdefault("scopes", []).append(entry)
    for name, value in (data.get("env") or {}).items():
        if literal_secret(name, value):
            rep.secret("{}:{}".format(relpath, line_of(lines, '"' + name + '"')), "env." + name, value, relpath)
    for key in ("apiKeyHelper",):
        if isinstance(data.get(key), str) and secret_in(data[key]):
            rep.secret("{}:{}".format(relpath, line_of(lines, key)), key, data[key], relpath)


def merge_claude(rep):
    scopes = sorted(rep.claude.get("scopes", []), key=lambda e: SCOPES.index(e["scope"]))
    if not scopes:
        return
    managed = [e for e in scopes if e["scope"] == "managed"]
    mdata = managed[0]["data"] if managed else {}
    rules_only_managed = (mdata.get("permissions") or {}).get("allowManagedPermissionRulesOnly") is True \
        or mdata.get("allowManagedPermissionRulesOnly") is True
    hooks_only_managed = mdata.get("allowManagedHooksOnly") is True
    eff = {"rules": {"allow": [], "ask": [], "deny": []}, "defaultMode": None, "sandbox": {},
           "hooks": [], "env": {}, "shell_settings": [], "plugins": {}, "marketplaces": [],
           "mcp_approval": {}, "additionalDirectories": [], "disableAllHooks": None,
           "disableBypass": None, "rules_only_managed": rules_only_managed, "hooks_only_managed": hooks_only_managed}

    def where(e, *needles):
        return "{}:{}".format(e["file"], line_of(e["lines"], *needles))

    for e in scopes:
        d, perms = e["data"], e["data"].get("permissions") or {}
        for kind in ("allow", "ask", "deny"):
            if rules_only_managed and e["scope"] != "managed":
                continue
            for r in perms.get(kind) or []:
                eff["rules"][kind].append({"rule": r, "where": where(e, json.dumps(r)[1:-1]), "scope": e["scope"]})
        if "defaultMode" in perms:
            eff["defaultMode"] = {"value": perms["defaultMode"], "where": where(e, "defaultMode"), "scope": e["scope"]}
        if "disableBypassPermissionsMode" in perms:
            eff["disableBypass"] = {"value": perms["disableBypassPermissionsMode"], "where": where(e, "disableBypassPermissionsMode")}
        for p in perms.get("additionalDirectories") or []:
            eff["additionalDirectories"].append({"path": p, "where": where(e, json.dumps(p)[1:-1])})
        sb = d.get("sandbox")
        if isinstance(sb, dict):
            def walk(obj, prefix):
                for k, v in obj.items():
                    key = prefix + k
                    if isinstance(v, dict):
                        walk(v, key + ".")
                    elif isinstance(v, list):
                        cur = eff["sandbox"].setdefault(key, {"value": [], "where": []})
                        cur["value"] = list(dict.fromkeys(cur["value"] + v))
                        cur["where"].append(where(e, '"' + k + '"'))
                    else:
                        eff["sandbox"][key] = {"value": v, "where": [where(e, '"' + k + '"')]}
            walk(sb, "")
        if "disableAllHooks" in d:
            eff["disableAllHooks"] = {"value": d["disableAllHooks"], "where": where(e, "disableAllHooks")}
        if not (hooks_only_managed and e["scope"] != "managed"):
            for event, groups in (d.get("hooks") or {}).items():
                for g in groups or []:
                    for h in (g.get("hooks") or []) if isinstance(g, dict) else []:
                        cmd = h.get("command") or h.get("url") or h.get("prompt") or ""
                        eff["hooks"].append({"event": event, "matcher": g.get("matcher", ""), "type": h.get("type", "command"),
                                             "command": cmd, "where": where(e, json.dumps(cmd)[1:30]) if cmd else where(e, event),
                                             "scope": e["scope"]})
        for k, v in (d.get("env") or {}).items():
            eff["env"][k] = {"value": v, "where": where(e, '"' + k + '"'), "scope": e["scope"]}
        for k in SHELL_KEYS:
            if k in d:
                v = d[k]
                cmd = v.get("command") if isinstance(v, dict) else v
                eff["shell_settings"] = [s for s in eff["shell_settings"] if s["key"] != k]
                eff["shell_settings"].append({"key": k, "command": cmd, "where": where(e, '"' + k + '"'), "scope": e["scope"]})
        for k, v in (d.get("enabledPlugins") or {}).items():
            eff["plugins"][k] = {"value": v, "where": where(e, '"' + k + '"')}
        for k, v in (d.get("extraKnownMarketplaces") or {}).items():
            eff["marketplaces"].append({"name": k, "source": v.get("source") if isinstance(v, dict) else v, "where": where(e, '"' + k + '"')})
        for k in ("enableAllProjectMcpServers", "enabledMcpjsonServers", "disabledMcpjsonServers"):
            if k in d:
                eff["mcp_approval"][k] = {"value": d[k], "where": where(e, k), "scope": e["scope"]}
    rep.claude["effective"] = eff

    # mechanical patterns
    allowed_wide = []
    for r in eff["rules"]["allow"]:
        wide, effect = classify_rule(r["rule"])
        if wide:
            allowed_wide.append(r)
            rep.flag("wide-allow", r["where"], r["rule"], effect)
    if eff["rules"]["deny"] and any(first_word((re.match(r"^Bash\((.*)\)$", r["rule"]) or [None, ""])[1]) in CODE_RUNNERS
                                    or r["rule"] == "Bash" for r in allowed_wide):
        runners = ", ".join(r["rule"] for r in allowed_wide if r["rule"].startswith("Bash"))
        denies = ", ".join(r["rule"] for r in eff["rules"]["deny"])
        rep.flag("deny-bypassable", eff["rules"]["deny"][0]["where"], denies,
                 "allowed without asking: {} - any of them can do what the deny list blocks".format(runners))
    dm = eff["defaultMode"]
    if dm and dm["value"] == "bypassPermissions":
        blocked = eff["disableBypass"] and eff["disableBypass"]["value"] == "disable"
        rep.flag("human-removed", dm["where"], "defaultMode: bypassPermissions (from {} scope)".format(dm["scope"]),
                 "every tool call runs without a prompt" + (" - but managed policy disables bypass mode" if blocked else ""))
    sb = eff["sandbox"]
    enabled = sb.get("enabled", {}).get("value") is True
    if not enabled:
        rep.flag("no-sandbox", (sb.get("enabled") or {}).get("where", ["(not set)"])[0], "sandbox.enabled not true",
                 "shell commands run with the user's full file and network access")
    else:
        if sb.get("allowUnsandboxedCommands", {}).get("value") is not False:
            w = (sb.get("allowUnsandboxedCommands") or {}).get("where", ["(not set; default allows retry)"])[0]
            rep.flag("sandbox-escape", w, "allowUnsandboxedCommands not false",
                     "a command that fails in the sandbox can retry outside it")
        if sb.get("excludedCommands", {}).get("value"):
            rep.flag("sandbox-escape", sb["excludedCommands"]["where"][0], ", ".join(sb["excludedCommands"]["value"]),
                     "these commands always run outside the sandbox")
        for d in (sb.get("network.allowedDomains") or {}).get("value", []):
            if d.strip() == "*" or d.startswith("*.") or any(x in d for x in RISKY_DOMAINS):
                rep.flag("wide-domain", sb["network.allowedDomains"]["where"][0], d,
                         "anyone can publish content at this host - a payload source and a place to send data")
    for h in eff["hooks"]:
        c = h["command"]
        if FETCH_WORD.search(c) and (PIPE_TO_SHELL.search(c) or RUN_DOWNLOADED.search(c)):
            rep.flag("hook-runs-remote", h["where"], c, "on {} it downloads code and runs it, without asking".format(h["event"]))
        elif FETCH_WORD.search(c):
            rep.flag("hook-network", h["where"], c, "on {} it reaches the network, without asking".format(h["event"]))
        else:
            rep.flag("hook", h["where"], c, "runs on {} ({}) without asking".format(h["event"], h["matcher"] or "every match"))
    for s in eff["shell_settings"]:
        rep.flag("runs-shell-setting", s["where"], "{}: {}".format(s["key"], s["command"]), "runs this command without asking")
    ap = eff["mcp_approval"].get("enableAllProjectMcpServers")
    if ap and ap["value"] is True:
        rep.flag("mcp-auto-approve", ap["where"], "enableAllProjectMcpServers: true",
                 "every server in .mcp.json starts without the user approving it")
    for k, v in eff["plugins"].items():
        if v["value"]:
            rep.flag("plugin", v["where"], k, "a plugin can bring hooks, MCP servers and subagents not visible in these files")


def scan_mcp_file(data, lines, relpath, tool, rep):
    if not isinstance(data, dict):
        return
    servers = data.get("mcpServers") or data.get("servers") or {}
    projects = data.get("projects") if relpath.endswith(".claude.json") else None
    blocks = [(relpath, servers)]
    if isinstance(projects, dict):
        for pname, p in projects.items():
            if isinstance(p, dict) and p.get("mcpServers"):
                blocks.append(("{} (local scope, {})".format(relpath, pname), p["mcpServers"]))
    for label, block in blocks:
        for name, s in (block or {}).items():
            if not isinstance(s, dict):
                continue
            ln = line_of(lines, '"' + name + '"')
            where = "{}:{}".format(relpath, ln)
            cmd, args, url = s.get("command", ""), [str(a) for a in s.get("args") or []], s.get("url", "")
            entry = {"tool": tool, "file": label, "name": name, "where": where, "command": cmd, "args": args,
                     "url": url, "type": s.get("type") or ("http" if url else "stdio"),
                     "env_keys": sorted((s.get("env") or {}).keys()), "header_keys": sorted((s.get("headers") or {}).keys())}
            rep.mcp.append(entry)
            check_server(entry, s, lines, relpath, rep)


def check_server(entry, s, lines, relpath, rep):
    cmd, args, where = entry["command"], entry["args"], entry["where"]
    launcher = os.path.basename(cmd)
    if launcher in ("npx", "bunx", "pnpm", "uvx", "pipx", "yarn"):
        pkgs = [a for a in args if not a.startswith("-") and a not in ("dlx", "run", "exec")]
        pkg = pkgs[0] if pkgs else ""
        version = pkg.rsplit("@", 1)[1] if pkg.count("@") > (1 if pkg.startswith("@") else 0) else ""
        if launcher == "uvx" and "==" in pkg:
            version = pkg.split("==", 1)[1]
        if not version or version in ("latest", "next") or re.search(r"[\^~*x]", version):
            rep.flag("unpinned-package", where, "{} {}".format(cmd, " ".join(args)),
                     "runs whatever `{}` the registry serves at start-up{}".format(pkg or "?", ", installed without asking (-y)" if "-y" in args or "--yes" in args else ""))
    if launcher in ("docker", "podman"):
        value_flags = ("-v", "--volume", "--mount", "-e", "--env", "--env-file", "-p", "--publish", "-w", "--workdir",
                       "--name", "--network", "-u", "--user", "--entrypoint", "-l", "--label", "--platform", "-h",
                       "--hostname", "--add-host")
        skip = {i + 1 for i, a in enumerate(args) if a in value_flags}
        image = next((a for i, a in enumerate(args)
                      if i not in skip and not a.startswith("-") and ("/" in a or ":" in a)), "")
        if image and "@sha256:" not in image and (":" not in image.split("/")[-1] or image.endswith(":latest")):
            rep.flag("unpinned-image", where, image, "runs whatever image the tag points at today")
        if any(a in ("--privileged", "--network=host") or a.startswith("/:/") or a.startswith("-v/") for a in args):
            rep.flag("container-host-access", where, " ".join(args), "the container reaches the host")
    if entry["url"] and entry["url"].startswith("http://") and "localhost" not in entry["url"] and "127.0.0.1" not in entry["url"]:
        rep.flag("plain-http", where, entry["url"], "credentials and data cross the network unencrypted")
    for group in ("env", "headers"):
        for k, v in (s.get(group) or {}).items():
            if literal_secret(k, v):
                rep.secret("{}:{}".format(relpath, line_of(lines, '"' + k + '"', str(v)[:6]) or line_of(lines, '"' + k + '"')),
                           "{}.{}.{}".format(entry["name"], group, k), v, relpath)
    for a in args + [entry["url"]]:
        if secret_in(a):
            rep.secret("{}:{}".format(relpath, line_of(lines, a[:12])), "{}.args".format(entry["name"]), a, relpath)


def scan_agent_file(path, relpath, scope, rep):
    text = read_text(path)
    if text is None:
        return
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.S)
    fm = {}
    if m:
        for ln in m.group(1).splitlines():
            if ":" in ln and not ln.startswith((" ", "\t", "-")):
                k, v = ln.split(":", 1)
                fm[k.strip()] = v.strip()
    tools = fm.get("tools")
    entry = {"file": relpath, "scope": scope, "name": fm.get("name", os.path.basename(path)[:-3]),
             "tools": tools, "permissionMode": fm.get("permissionMode"), "model": fm.get("model")}
    rep.agents.append(entry)
    lines = text.splitlines()
    if not tools:
        rep.flag("inherits-all-tools", "{}:{}".format(relpath, line_of(lines, "name:") or 1), entry["name"],
                 "no tools: list - it gets every tool the main session has, MCP servers included")
    elif re.search(r"\bBash\b(?!\()", tools):
        rep.flag("wide-allow", "{}:{}".format(relpath, line_of(lines, "tools:")), tools, "this subagent holds an unrestricted shell")
    if entry["permissionMode"] in ("bypassPermissions", "acceptEdits"):
        rep.flag("human-removed" if entry["permissionMode"] == "bypassPermissions" else "fewer-prompts",
                 "{}:{}".format(relpath, line_of(lines, "permissionMode")), "permissionMode: " + entry["permissionMode"],
                 "this subagent's tool calls run without a prompt" if entry["permissionMode"] == "bypassPermissions"
                 else "this subagent's file edits run without a prompt")
    if HIDDEN_CHARS.search(text):
        rep.flag("hidden-characters", relpath, "{} invisible characters".format(len(HIDDEN_CHARS.findall(text))),
                 "text the user can't see is in the agent's instructions")


def scan_codex(data, lines, relpath, rep):
    if not isinstance(data, dict):
        return

    def one(label, d, prefix):
        sww = d.get("sandbox_workspace_write") or {}
        entry = {"file": relpath, "profile": label, "approval_policy": d.get("approval_policy"),
                 "sandbox_mode": d.get("sandbox_mode"), "network_access": sww.get("network_access"),
                 "writable_roots": sww.get("writable_roots"),
                 "env_inherit": (d.get("shell_environment_policy") or {}).get("inherit")}
        rep.codex.append(entry)
        w = lambda key: "{}:{}".format(relpath, line_of(lines, key) if not prefix else profile_line(lines, label, key))
        if entry["sandbox_mode"] == "danger-full-access":
            rep.flag("human-removed" if entry["approval_policy"] == "never" else "no-sandbox", w("sandbox_mode"),
                     "{}sandbox_mode = danger-full-access".format(prefix),
                     "commands run with the user's full file and network access" +
                     (" and approval_policy = never: nobody is asked" if entry["approval_policy"] == "never" else ""))
        elif entry["approval_policy"] == "never":
            rep.flag("fewer-prompts", w("approval_policy"), prefix + "approval_policy = never",
                     "nothing is ever escalated to a person; the sandbox is the only control")
        if entry["network_access"] is True:
            rep.flag("network-on", w("network_access"), prefix + "sandbox_workspace_write.network_access = true",
                     "sandboxed commands reach any host")
        if entry["env_inherit"] == "all":
            rep.flag("env-inherit", w("inherit"), prefix + 'shell_environment_policy.inherit = "all"',
                     "every environment variable, tokens included, is passed to every command")

    one("(top level)", data, "")
    for name, prof in (data.get("profiles") or {}).items():
        if isinstance(prof, dict):
            one(name, prof, "profiles.{}.".format(name))
    if data.get("profile"):
        rep.notes.append("{}: default profile is `{}` - its values override the top level".format(relpath, data["profile"]))
    for name, s in (data.get("mcp_servers") or {}).items():
        if isinstance(s, dict):
            entry = {"tool": "codex", "file": relpath, "name": name,
                     "where": "{}:{}".format(relpath, line_of(lines, "mcp_servers." + name) or line_of(lines, name)),
                     "command": s.get("command", ""), "args": [str(a) for a in s.get("args") or []], "url": s.get("url", ""),
                     "type": "http" if s.get("url") else "stdio", "env_keys": sorted((s.get("env") or {}).keys()),
                     "header_keys": sorted((s.get("http_headers") or {}).keys())}
            rep.mcp.append(entry)
            s2 = dict(s, headers=s.get("http_headers"))
            check_server(entry, s2, lines, relpath, rep)


def profile_line(lines, profile, key):
    start = line_of(lines, "[profiles.{}".format(profile)) or line_of(lines, 'profiles."{}"'.format(profile))
    for i in range(start, len(lines)):
        if i > start and lines[i].lstrip().startswith("[") and "profiles.{}".format(profile) not in lines[i]:
            break
        if lines[i].lstrip().startswith(key) or key in lines[i]:
            return i + 1
    return start


def scan_vscode(data, lines, relpath, rep):
    if not isinstance(data, dict):
        return
    for k in ("chat.tools.autoApprove", "chat.tools.global.autoApprove"):
        if data.get(k) is True:
            rep.flag("human-removed", "{}:{}".format(relpath, line_of(lines, k)), k + ": true", "every agent tool call runs without a prompt")
    for k in ("chat.tools.terminal.autoApprove", "github.copilot.chat.agent.terminal.allowList", "chat.agent.terminal.allowList"):
        v = data.get(k)
        if isinstance(v, dict):
            for cmd, ok in v.items():
                c = cmd.strip("/^$ ").split(" ")[0]
                if ok is True and (c in CODE_RUNNERS or cmd.strip() in ("/.*/", ".*", "*")):
                    rep.flag("wide-allow", "{}:{}".format(relpath, line_of(lines, json.dumps(cmd)[1:-1])), "{}: {}".format(k, cmd),
                             CODE_RUNNERS.get(c, "any command") + ", run without a prompt")
        rep.vscode.append({"file": relpath, "key": k, "value": v}) if v is not None else None
    for k in ("chat.tools.autoApprove", "chat.agent.enabled", "chat.mcp.autostart", "chat.mcp.discovery.enabled"):
        if k in data:
            rep.vscode.append({"file": relpath, "key": k, "value": data[k]})


def scan_rules(path, relpath, rep):
    text = read_text(path)
    if text is None:
        return
    hidden = HIDDEN_CHARS.findall(text)
    lines = text.splitlines()
    runs = [i for i, ln in enumerate(lines, 1) if FETCH_WORD.search(ln) and re.search(r"\b(run|execute|always|before)\b", ln, re.I)]
    rep.cursor_rules.append({"file": relpath, "hidden_chars": len(hidden), "lines_that_fetch_or_run": runs})
    if hidden:
        rep.flag("hidden-characters", relpath, "{} invisible characters".format(len(hidden)), "text the user can't see is in the agent's rules")
    for i in runs:
        rep.flag("rule-runs-remote", "{}:{}".format(relpath, i), lines[i - 1].strip()[:140], "the rules tell the agent to fetch or run something")


def scan_secrets_plain(path, relpath, rep):
    text = read_text(path)
    if text is None:
        return
    for i, ln in enumerate(text.splitlines(), 1):
        m = re.match(r"^\s*(export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*[=:]\s*(.*)$", ln)
        if m:
            val = m.group(3).strip().strip("\"'")
            if literal_secret(m.group(2), val):
                rep.secret("{}:{}".format(relpath, i), m.group(2), val, relpath)
                continue
        for p in SECRET_PATTERNS:
            s = p.search(ln)
            if s:
                rep.secret("{}:{}".format(relpath, i), "(in text)", s.group(0), relpath)
                break


def scan_launch(path, relpath, rep):
    text = read_text(path)
    if text is None:
        return
    for i, ln in enumerate(text.splitlines(), 1):
        for f in LAUNCH_FLAGS:
            if f in ln:
                rep.launch.append({"where": "{}:{}".format(relpath, i), "flag": f, "text": ln.strip()[:140]})
                if f in ("dangerously-skip-permissions", "dangerously-bypass-approvals-and-sandbox", "--yolo"):
                    rep.flag("human-removed", "{}:{}".format(relpath, i), ln.strip()[:140], "launches the agent with every prompt switched off")
                break


def gitignore_patterns(root):
    text = read_text(os.path.join(root, ".gitignore")) or ""
    return [p.strip() for p in text.splitlines() if p.strip() and not p.strip().startswith("#")]


def ignored(relpath, patterns):
    """Approximate .gitignore match (no negation precedence beyond last-match-wins)."""
    hit = False
    rp = relpath.replace(os.sep, "/")
    for p in patterns:
        neg = p.startswith("!")
        pat = p[1:] if neg else p
        pat = pat.rstrip("/")
        anchored = pat.startswith("/") or "/" in pat.strip("/")
        pat = pat.lstrip("/")
        cands = [rp] if anchored else [rp, os.path.basename(rp)] + ["/".join(rp.split("/")[i:]) for i in range(len(rp.split("/")))]
        if any(fnmatch.fnmatch(c, pat) or fnmatch.fnmatch(c, pat + "/*") or c.startswith(pat + "/") for c in cands):
            hit = not neg
    return hit


def discover_project(root, rep):
    def p(*parts):
        return os.path.join(root, *parts)
    found = []
    for f, kind, scope in ((".claude/settings.json", "claude", "project"), (".claude/settings.local.json", "claude", "local"),
                           ("managed-settings.json", "claude", "managed"),
                           (".mcp.json", "mcp", "claude"), (".cursor/mcp.json", "mcp", "cursor"),
                           (".vscode/mcp.json", "mcp", "vscode"), (".vscode/settings.json", "vscode", None),
                           (".codex/config.toml", "codex", None), ("config.toml", "codex?", None),
                           (".cursorrules", "rules", None), ("AGENTS.md", "rules", None), ("CLAUDE.md", "rules", None)):
        if os.path.isfile(p(f)):
            found.append((p(f), kind, scope))
    for d, kind in ((".claude/agents", "agent"), (".cursor/rules", "rules"), (".github/workflows", "launch"), (".devcontainer", "launch")):
        if os.path.isdir(p(d)):
            for dirpath, _, files in os.walk(p(d)):
                for fn in sorted(files):
                    if kind == "agent" and not fn.endswith(".md"):
                        continue
                    found.append((os.path.join(dirpath, fn), kind, "project"))
    for fn in ("package.json", "Makefile", "justfile", "docker-compose.yml"):
        if os.path.isfile(p(fn)):
            found.append((p(fn), "launch", None))
    for fn in sorted(os.listdir(root)):
        if fn.endswith(".sh") and os.path.isfile(p(fn)):
            found.append((p(fn), "launch", None))
    return found


def discover_user(home):
    out = []
    for f, kind, scope in ((".claude/settings.json", "claude", "user"), (".claude.json", "mcp", "claude-user"),
                           (".codex/config.toml", "codex", None), (".cursor/mcp.json", "mcp", "cursor-user")):
        if os.path.isfile(os.path.join(home, f)):
            out.append((os.path.join(home, f), kind, scope))
    ad = os.path.join(home, ".claude", "agents")
    if os.path.isdir(ad):
        out += [(os.path.join(ad, f), "agent", "user") for f in sorted(os.listdir(ad)) if f.endswith(".md")]
    return out


def mcp_tool(path):
    parts = path.replace(os.sep, "/").split("/")
    if ".cursor" in parts:
        return "cursor"
    if ".vscode" in parts:
        return "vscode"
    return "claude"


def classify_file(path):
    b = os.path.basename(path)
    if b == "settings.local.json":
        return "claude", "local"
    if b == "managed-settings.json":
        return "claude", "managed"
    if b == "settings.json" and os.path.basename(os.path.dirname(path)) == ".vscode":
        return "vscode", None
    if b == "settings.json":
        return "claude", "project"
    if b in (".mcp.json", "mcp.json", ".claude.json"):
        return "mcp", "given"
    if b.endswith(".toml"):
        return "codex", None
    if b.endswith((".mdc",)) or b == ".cursorrules":
        return "rules", None
    if b.endswith(".md") and os.path.basename(os.path.dirname(path)) == "agents":
        return "agent", "project"
    return "plain", None


def run(args):
    rep = Report()
    items, base = [], os.getcwd()
    roots = [a for a in args.paths if os.path.isdir(a)]
    if len(roots) == 1 and len(args.paths) == 1:
        base = os.path.abspath(roots[0])
    for a in args.paths:
        if os.path.isdir(a):
            items += discover_project(a, rep)
        elif os.path.isfile(a):
            k, s = classify_file(a)
            items.append((a, k, s))
        else:
            rep.notes.append("{}: not found".format(a))
    if args.user:
        items += discover_user(args.user)
    if args.managed:
        items.append((args.managed, "claude", "managed"))
    for a in args.also or []:
        items.append((a, "plain", None))
    seen = set()
    for path, kind, scope in items:
        ap = os.path.abspath(path)
        if ap in seen:
            continue
        seen.add(ap)
        r = rel(ap, base)
        if args.user and ap.startswith(os.path.abspath(args.user) + os.sep):
            r = "~/" + os.path.relpath(ap, os.path.abspath(args.user))
        if kind == "claude":
            data, lines = load_json(path, rep.notes)
            scan_claude_settings(data, lines, scope, r, rep)
        elif kind == "mcp":
            data, lines = load_json(path, rep.notes)
            scan_mcp_file(data, lines, r, mcp_tool(ap), rep)
        elif kind == "vscode":
            data, lines = load_json(path, rep.notes)
            scan_vscode(data, lines, r, rep)
        elif kind in ("codex", "codex?"):
            data, lines = load_toml(path, rep.notes)
            if kind == "codex?" and not (isinstance(data, dict) and any(k in data for k in ("approval_policy", "sandbox_mode", "profiles", "mcp_servers", "model_provider"))):
                continue
            scan_codex(data, lines, r, rep)
        elif kind == "agent":
            scan_agent_file(path, r, scope, rep)
        elif kind == "rules":
            scan_rules(path, r, rep)
        elif kind == "launch":
            scan_launch(path, r, rep)
        elif kind == "plain":
            scan_secrets_plain(path, r, rep)
        rep.files.append({"file": r, "kind": kind.rstrip("?"), "scope": scope})
    merge_claude(rep)
    # git-ignore status of local files and of files holding secrets
    if roots:
        pats = gitignore_patterns(roots[0])
        rep.claude["gitignore_found"] = os.path.isfile(os.path.join(roots[0], ".gitignore"))
        check = {f["file"] for f in rep.files if f["scope"] == "local"} | {s["file"] for s in rep.secrets}
        for f in sorted(check):
            if f.startswith("~/") or os.path.isabs(f):
                continue
            ig = ignored(f, pats)
            for s in rep.secrets:
                if s["file"] == f:
                    s["gitignored"] = ig
            if not ig:
                rep.flag("not-ignored", f, f, "not matched by .gitignore, so it can be committed" +
                         (" - and it holds a literal secret" if any(s["file"] == f for s in rep.secrets) else ""))
    for s in rep.secrets:
        state = s.get("gitignored")
        rep.flag("literal-secret", s["where"], "{} = {}".format(s["name"], s["masked"]),
                 "a credential written into the file in plain text" +
                 {True: " (git-ignored, but readable by anything that reads the folder)",
                  False: "; the file is not git-ignored, so anyone with the repo has it"}.get(state, ""))
    return rep


def render(rep):
    out = ["# Agent configuration scan", "", "Mechanical listing only: what the files grant, merged the way the tools merge them. "
           "Severity and the verdict are the reviewer's call.", ""]
    out.append("## Files read")
    for f in rep.files:
        out.append("- `{}` - {}{}".format(f["file"], f["kind"], " ({} scope)".format(f["scope"]) if f["scope"] in SCOPES else ""))
    seen_scopes = {e["scope"] for e in rep.claude.get("scopes", [])}
    missing = [s for s in SCOPES if s not in seen_scopes]
    if rep.claude.get("scopes") and missing:
        out.append("- Claude Code scopes not read: {} - the effective result below can only be wider than shown".format(", ".join(missing)))
    for n in rep.notes:
        out.append("- note: " + n)
    out.append("")
    eff = rep.claude.get("effective")
    if eff:
        out += ["## Claude Code, effective (scopes merged: user < project < local < managed; rules add up, deny > ask > allow)", ""]
        if eff["rules_only_managed"]:
            out.append("- managed policy: only managed permission rules apply")
        dm = eff["defaultMode"]
        out.append("- defaultMode: {}".format("`{}` from {} scope ({})".format(dm["value"], dm["scope"], dm["where"]) if dm else "not set (default: ask)"))
        for kind in ("allow", "ask", "deny"):
            rules = eff["rules"][kind]
            out.append("- {} ({}): {}".format(kind, len(rules), "; ".join("`{}` {}".format(r["rule"], r["where"]) for r in rules) or "none"))
        if eff["additionalDirectories"]:
            out.append("- additionalDirectories: " + "; ".join("`{}` {}".format(d["path"], d["where"]) for d in eff["additionalDirectories"]))
        if eff["sandbox"]:
            out.append("- sandbox: " + "; ".join("{} = {} ({})".format(k, json.dumps(v["value"]), ", ".join(v["where"])) for k, v in sorted(eff["sandbox"].items())))
        else:
            out.append("- sandbox: not configured in any scope read")
        out.append("- hooks ({}):".format(len(eff["hooks"])) if eff["hooks"] else "- hooks: none")
        for h in eff["hooks"]:
            out.append("  - {} [{}] {} scope, {}: `{}`".format(h["event"], h["matcher"] or "*", h["scope"], h["where"], h["command"]))
        if eff["disableAllHooks"]:
            out.append("- disableAllHooks: {} ({})".format(eff["disableAllHooks"]["value"], eff["disableAllHooks"]["where"]))
        for s in eff["shell_settings"]:
            out.append("- {} runs: `{}` ({})".format(s["key"], s["command"], s["where"]))
        if eff["env"]:
            out.append("- env: " + "; ".join("{}={} ({})".format(k, mask(v["value"]) if literal_secret(k, v["value"]) else json.dumps(v["value"]), v["where"]) for k, v in eff["env"].items()))
        for k, v in eff["mcp_approval"].items():
            out.append("- {}: {} ({})".format(k, json.dumps(v["value"]), v["where"]))
        for k, v in eff["plugins"].items():
            out.append("- plugin `{}` enabled={} ({})".format(k, v["value"], v["where"]))
        for m in eff["marketplaces"]:
            out.append("- marketplace `{}`: {} ({})".format(m["name"], json.dumps(m["source"]), m["where"]))
        out.append("")
    if rep.mcp:
        out += ["## MCP servers", ""]
        for s in rep.mcp:
            how = s["url"] or " ".join([s["command"]] + s["args"])
            extra = []
            if s["env_keys"]:
                extra.append("env: " + ", ".join(s["env_keys"]))
            if s["header_keys"]:
                extra.append("headers: " + ", ".join(s["header_keys"]))
            out.append("- `{}` ({}, {}) {}: `{}`{}".format(s["name"], s["tool"], s["type"], s["where"], how, " - " + "; ".join(extra) if extra else ""))
        out.append("")
    if rep.agents:
        out += ["## Subagents", ""]
        for a in rep.agents:
            out.append("- `{}` ({}): tools: {}; permissionMode: {}; model: {}".format(
                a["name"], a["file"], a["tools"] or "NONE LISTED - inherits everything", a["permissionMode"] or "default", a["model"] or "inherit"))
        out.append("")
    if rep.codex:
        out += ["## Codex", ""]
        for c in rep.codex:
            out.append("- {} {}: approval_policy={}, sandbox_mode={}, network_access={}, env inherit={}".format(
                c["file"], c["profile"], c["approval_policy"], c["sandbox_mode"], c["network_access"], c["env_inherit"]))
        out.append("")
    if rep.vscode:
        out += ["## VS Code / Copilot", ""] + ["- {} {}: {}".format(v["file"], v["key"], json.dumps(v["value"])) for v in rep.vscode] + [""]
    if rep.cursor_rules:
        out += ["## Rules files", ""] + ["- {}: {} invisible characters; lines that fetch or run: {}".format(
            r["file"], r["hidden_chars"], r["lines_that_fetch_or_run"] or "none") for r in rep.cursor_rules] + [""]
    if rep.launch:
        out += ["## Launch flags in scripts", ""] + ["- {}: `{}`".format(l["where"], l["text"]) for l in rep.launch] + [""]
    out += ["## Literal secrets (masked)", ""]
    out += ["- {} `{}` = {}{}".format(s["where"], s["name"], s["masked"], "" if "gitignored" not in s else (" (git-ignored)" if s["gitignored"] else " (NOT git-ignored)")) for s in rep.secrets] or ["- none found"]
    out += ["", "## Patterns to grade ({})".format(len(rep.flags)), ""]
    order = ["literal-secret", "hook-runs-remote", "human-removed", "deny-bypassable", "wide-allow", "no-sandbox", "sandbox-escape",
             "rule-runs-remote", "hidden-characters", "unpinned-package", "unpinned-image", "inherits-all-tools", "mcp-auto-approve",
             "wide-domain", "env-inherit", "network-on", "hook-network", "runs-shell-setting", "hook", "not-ignored", "plugin",
             "fewer-prompts", "container-host-access", "plain-http"]
    for f in sorted(rep.flags, key=lambda f: order.index(f["kind"]) if f["kind"] in order else 99):
        out.append("- [{}] {} `{}` - {}".format(f["kind"], f["where"], f["text"], f["effect"]))
    if not rep.flags:
        out.append("- none")
    return "\n".join(out) + "\n"


def to_json(rep):
    eff = rep.claude.get("effective")
    return json.dumps({"files": rep.files, "notes": rep.notes, "claude_effective": eff, "mcp_servers": rep.mcp,
                       "subagents": rep.agents, "codex": rep.codex, "vscode": rep.vscode, "rules": rep.cursor_rules,
                       "launch_flags": rep.launch, "secrets": rep.secrets, "patterns": rep.flags}, indent=2, default=str)


def main(argv=None):
    ap = argparse.ArgumentParser(description="List what a coding agent's configuration grants (mechanical layer for a review).")
    ap.add_argument("paths", nargs="+", help="project folders or config files")
    ap.add_argument("--user", help="home folder to read user-scope config from")
    ap.add_argument("--managed", help="managed-settings.json (organisation policy)")
    ap.add_argument("--also", nargs="*", help="other files a config references, searched for literal secrets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of markdown")
    ap.add_argument("-o", "--out", help="write the report here instead of stdout")
    args = ap.parse_args(argv)
    if not any(os.path.exists(p) for p in args.paths):
        print("error: none of the paths exist: " + ", ".join(args.paths), file=sys.stderr)
        return 2
    rep = run(args)
    if not rep.files:
        print("error: no agent configuration files found in " + ", ".join(args.paths), file=sys.stderr)
        return 1
    text = redact(to_json(rep) if args.json else render(rep))
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text)
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())

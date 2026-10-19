/* Organisation governance (RFC-0050, OWASP AST09): a policy the installer enforces, an audit
   log that shows when its history was edited, and a check that a mirror still matches what was
   packaged. Node's standard library only, like the rest of the CLI.

   The policy is a JSON file an organisation hands out (MDM, a dotfiles repo, an image):
     --policy <file>  >  SKILLDROP_POLICY  >  ~/.config/skilldrop/policy.json
   A policy that is named but missing, unreadable, or carries a key this version doesn't know
   stops the command: a policy that fails open is not a policy. */
"use strict";
const fs = require("fs");
const path = require("path");
const os = require("os");
const crypto = require("crypto");
const { execFileSync } = require("child_process");

const SEVERITY = { "🟥": 3, "🟧": 2, "🟨": 1 };          // scan findings; ⚪ (fixtures) never count
const MAX = { none: 0, low: 1, medium: 2, high: 3 };      // policy scan.max: the worst finding allowed
const KEYS = {
  "": ["version", "catalogues", "skills", "scan", "audit", "require_containment", "note"],
  catalogues: ["allow", "require_pinned"],
  skills: ["allow", "block"],
  scan: ["max"],
  audit: ["log", "actor", "salt_env"],
};

function die(msg) { console.error(`error: ${msg}`); process.exit(1); }
const sha256 = (s) => crypto.createHash("sha256").update(s).digest("hex");
const tilde = (p) => (p.startsWith(os.homedir()) ? "~" + p.slice(os.homedir().length) : p);
const untilde = (p) => (p.startsWith("~/") ? path.join(os.homedir(), p.slice(2)) : p);

function policyPath(flags) {
  if (flags.policy && flags.policy !== true) return { file: path.resolve(String(flags.policy)), named: true };
  if (process.env.SKILLDROP_POLICY) return { file: path.resolve(untilde(process.env.SKILLDROP_POLICY)), named: true };
  const dflt = path.join(os.homedir(), ".config", "skilldrop", "policy.json");
  return { file: dflt, named: false };
}

/* The policy in force, or null when none is set. */
function load(flags) {
  const { file, named } = policyPath(flags || {});
  if (!fs.existsSync(file)) {
    if (named) die(`policy ${file} does not exist — nothing was changed`);
    return null;
  }
  let raw, p;
  try { raw = fs.readFileSync(file, "utf8"); p = JSON.parse(raw); }
  catch (e) { die(`policy ${file} is not valid JSON (${e.message}) — nothing was changed`); }
  const problems = [];
  const closed = (obj, where) => {
    if (obj === undefined) return;
    if (!obj || typeof obj !== "object" || Array.isArray(obj)) return problems.push(`${where || "the policy"} must be an object`);
    for (const k of Object.keys(obj)) if (!KEYS[where].includes(k)) problems.push(`unknown key '${where ? where + "." : ""}${k}'`);
  };
  closed(p, "");
  for (const k of ["catalogues", "skills", "scan", "audit"]) closed(p[k], k);
  if (p.version !== 1) problems.push("version must be 1");
  const list = (v, where) => { if (v !== undefined && !(Array.isArray(v) && v.every((x) => typeof x === "string"))) problems.push(`${where} must be a list of strings`); };
  list(p.catalogues && p.catalogues.allow, "catalogues.allow");
  list(p.skills && p.skills.allow, "skills.allow");
  list(p.skills && p.skills.block, "skills.block");
  if (p.catalogues && p.catalogues.require_pinned !== undefined && typeof p.catalogues.require_pinned !== "boolean")
    problems.push("catalogues.require_pinned must be true or false");
  if (p.require_containment !== undefined && typeof p.require_containment !== "boolean")
    problems.push("require_containment must be true or false");
  if (p.scan && p.scan.max !== undefined && !(p.scan.max in MAX)) problems.push(`scan.max must be one of ${Object.keys(MAX).join(", ")}`);
  if (p.audit) {
    const a = p.audit.actor;
    const ok = a === undefined || ["none", "pseudonym", "os-user"].includes(a) ||
               (a && typeof a === "object" && Object.keys(a).length === 1 && typeof a.fixed === "string" && a.fixed.trim());
    if (!ok) problems.push('audit.actor must be "none", "pseudonym", "os-user" or {"fixed": "<name>"}');
    if (p.audit.log !== undefined && typeof p.audit.log !== "string") problems.push("audit.log must be a path");
  }
  if (problems.length) die(`policy ${file} is not usable — nothing was changed:\n  ${problems.join("\n  ")}`);
  return Object.assign(p, { file, hash: sha256(raw).slice(0, 16) });
}

const glob = (pat) => new RegExp("^" + pat.split("*").map((s) => s.replace(/[.+?^${}()|[\]\\]/g, "\\$&")).join(".*") + "$", "i");
const matches = (name, pats) => (pats || []).some((p) => glob(p).test(name));

/* A catalogue source as the policy compares it: "bundled", an absolute path, or a git URL
   without its #ref, trailing slash or .git. */
function sourceKey(source) {
  if (!source || source === "bundled") return "bundled";
  const i = source.lastIndexOf("#");
  const url = i > 0 ? source.slice(0, i) : source;
  if (fs.existsSync(url)) return path.resolve(url);
  return url.replace(/\/+$/, "").replace(/\.git$/i, "");
}

/* Why the policy refuses these units, as [{name, why}]; an empty list means allowed.
   worst: {name: "🟥" | "🟧" | "🟨" | undefined}, the worst scan finding per unit. */
function check(policy, { source, pinned, names, worst = {}, kind = "skill" }) {
  if (!policy) return [];
  const out = [];
  const key = sourceKey(source);
  const cats = policy.catalogues || {};
  if (cats.allow && !cats.allow.some((a) => (a === "bundled" ? key === "bundled" : matches(key, [sourceKey(a)]))))
    for (const n of names) out.push({ name: n, why: `catalogue '${key}' is not in the policy's allowed list` });
  else if (cats.require_pinned && key !== "bundled" && !pinned)
    for (const n of names) out.push({ name: n, why: `catalogue '${key}' must be pinned to a commit (--from <url>#<commit>)` });
  const sk = policy.skills || {};
  for (const n of names) {
    if (matches(n, sk.block)) out.push({ name: n, why: `${kind} '${n}' is blocked by the policy` });
    else if (sk.allow && !matches(n, sk.allow)) out.push({ name: n, why: `${kind} '${n}' is not in the policy's allowed list` });
    const max = policy.scan && policy.scan.max;
    if (max !== undefined && worst[n] && SEVERITY[worst[n]] > MAX[max])
      out.push({ name: n, why: `the supply-chain scan found a ${worst[n]} pattern, above the policy's limit (${max})` });
  }
  return out;
}

/* ---------- audit log ----------
   One JSON object per line. Each line carries the SHA-256 of the line before it, so a line
   edited or removed afterwards breaks the chain, and `skilldrop audit verify` says where. */
function auditFile(policy) {
  const env = process.env.SKILLDROP_AUDIT_LOG;
  if (!(policy && policy.audit) && !env) return null;
  const f = path.resolve(untilde(env || (policy.audit.log || "~/.config/skilldrop/audit.jsonl")));
  // Never inside a git working tree, where it could be committed.
  try {
    const dir = path.dirname(f);
    fs.mkdirSync(dir, { recursive: true });
    const top = execFileSync("git", ["rev-parse", "--show-toplevel"], { cwd: dir, encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] }).trim();
    if (top) die(`the audit log ${tilde(f)} is inside a git working tree (${tilde(top)}); keep it outside any repository`);
  } catch (e) { /* not inside a repository (or no git): good */ }
  return f;
}

function actor(policy) {
  const mode = (policy && policy.audit && policy.audit.actor) || "pseudonym";
  if (mode === "none") return null;
  if (typeof mode === "object") return mode.fixed;
  const user = (() => { try { return os.userInfo().username; } catch (e) { return "unknown"; } })();
  if (mode === "os-user") return user;
  const saltVar = (policy && policy.audit && policy.audit.salt_env) || "SKILLDROP_AUDIT_SALT";
  const salt = process.env[saltVar];
  if (!salt) die(`the audit log names people by pseudonym, which needs a secret salt: set ${saltVar} (the organisation keeps it), or set audit.actor to "none"`);
  return "p:" + crypto.createHmac("sha256", salt).update(`${user}@${os.hostname()}`).digest("hex").slice(0, 16);
}

function lastLine(f) {
  if (!fs.existsSync(f)) return null;
  const lines = fs.readFileSync(f, "utf8").split("\n").filter(Boolean);
  return lines.length ? lines[lines.length - 1] : null;
}

/* Everything the audit log needs (where it goes, who is acting), worked out before a command
   changes anything: an install must not land and then fail to be recorded. */
const ready = new Map();
function prepare(policy) {
  const key = policy || "env";
  if (ready.has(key)) return ready.get(key);
  const f = auditFile(policy);
  const r = f ? { f, who: actor(policy) } : null;
  ready.set(key, r);
  return r;
}

/* Append one event per unit. Does nothing when no audit log is configured. */
function audit(policy, action, units, extra) {
  const r = prepare(policy);
  if (!r || !units.length) return;
  const { f, who } = r;
  for (const u of units) {
    const prev = lastLine(f);
    const entry = Object.assign({ ts: new Date().toISOString(), action }, u, extra || {},
      { actor: who, policy: policy ? policy.hash : null, prev: prev ? sha256(prev) : "0".repeat(64) });
    if (entry.target) entry.target = tilde(entry.target);
    if (entry.source) entry.source = tilde(entry.source);  // a catalogue on local disk names no home directory
    fs.appendFileSync(f, JSON.stringify(entry) + "\n", { mode: 0o600 });
  }
}

function verifyAudit(file) {
  const f = path.resolve(untilde(file));
  if (!fs.existsSync(f)) die(`no audit log at ${tilde(f)}`);
  const lines = fs.readFileSync(f, "utf8").split("\n").filter(Boolean);
  let prev = "0".repeat(64);
  for (let i = 0; i < lines.length; i++) {
    let e;
    try { e = JSON.parse(lines[i]); } catch (err) { return { ok: false, line: i + 1, why: "not valid JSON", count: lines.length }; }
    if (e.prev !== prev) return { ok: false, line: i + 1, why: "does not follow the line before it: a line was edited, removed or inserted", count: lines.length };
    prev = sha256(lines[i]);
  }
  return { ok: true, count: lines.length };
}

/* ---------- mirrors ----------
   MIRROR.json (skilldrop package) records a SHA-256 for every file it copied. */
function verifyMirror(dir) {
  const root = path.resolve(dir);
  const mf = path.join(root, "MIRROR.json");
  if (!fs.existsSync(mf)) die(`${root} has no MIRROR.json — it wasn't made by skilldrop package`);
  let m;
  try { m = JSON.parse(fs.readFileSync(mf, "utf8")); } catch (e) { die(`${mf} is not valid JSON`); }
  const want = m.files || {};
  const found = {};
  const walk = (d) => {
    for (const e of fs.readdirSync(d, { withFileTypes: true })) {
      if (e.name === ".git") continue;
      const p = path.join(d, e.name);
      if (e.isDirectory()) walk(p);
      else found[path.relative(root, p).split(path.sep).join("/")] = p;
    }
  };
  walk(root);
  const own = new Set(["MIRROR.json", "catalogue.json"]);
  const missing = Object.keys(want).filter((f) => !found[f]);
  const changed = Object.keys(want).filter((f) => found[f] && sha256(fs.readFileSync(found[f])) !== want[f]);
  const extra = Object.keys(found).filter((f) => !(f in want) && !own.has(f) && !/^packs\/[^/]+\/pack\.json$/.test(f));
  return { source: m.source, created: m.created, files: Object.keys(want).length, missing, changed, extra };
}

/* ---------- containment (RFC-0051, OWASP AST06) ----------
   Claude Code's sandbox confines the shell commands a session runs, and every process they
   start: writes to the working directory and temp, network only to allowed hosts. It applies
   to a whole project session, not to one skill, so containing a skill means turning the strict
   sandbox on for the project it is installed into, sized to what its manifest declares
   (permissions.network, permissions.files). It only ever adds restrictions: it never removes
   a setting, never sets one to something looser, and never widens a sandbox that is already
   on. Facts from code.claude.com/docs/en/sandboxing and /permissions, checked 2026-10-19. */
function readSettings(f) {
  if (!f || !fs.existsSync(f)) return {};
  try { return JSON.parse(fs.readFileSync(f, "utf8")); }
  catch (e) { die(`${tilde(f)} is not valid JSON — fix it before containment changes it; nothing was installed`); }
}
const strictIn = (d) => !!(d && d.sandbox && d.sandbox.enabled === true && d.sandbox.allowUnsandboxedCommands === false);

/* units: [{name, perms}]; files: {local, project, user}; opts: {require}.
   Returns what --contain would change, without writing anything. */
function containmentPlan(units, files, opts = {}) {
  const uncontainable = units.filter((u) => u.perms && u.perms.files === "anywhere").map((u) => u.name);
  const hosts = [...new Set(units.flatMap((u) => (u.perms && u.perms.network) || []))].sort();
  const local = readSettings(files.local);
  const others = [files.project, files.user].filter((f) => f && f !== files.local).map(readSettings);
  const before = JSON.stringify(local);
  const next = JSON.parse(before);
  const sb = (next.sandbox = next.sandbox && typeof next.sandbox === "object" ? next.sandbox : {});
  const alreadyOn = sb.enabled === true || others.some((d) => d.sandbox && d.sandbox.enabled === true);
  const changes = [], notes = [];
  if (sb.enabled !== true) { sb.enabled = true; changes.push("sandbox.enabled: true — shell commands and what they start run in the OS sandbox"); }
  if (sb.allowUnsandboxedCommands !== false) {
    sb.allowUnsandboxedCommands = false;
    changes.push("sandbox.allowUnsandboxedCommands: false — a command that fails in the sandbox can't retry outside it");
  }
  if (opts.require && sb.failIfUnavailable !== true) {
    sb.failIfUnavailable = true;
    changes.push("sandbox.failIfUnavailable: true — Claude Code won't start here if the sandbox can't (the policy requires containment)");
  }
  if (hosts.length && alreadyOn)
    notes.push(`these skills declare network hosts (${hosts.join(", ")}). The sandbox was already on, so they were not added: ` +
               "adding hosts would widen it. Add them to sandbox.network.allowedDomains yourself if the skills should reach them.");
  else if (hosts.length) {
    sb.network = sb.network && typeof sb.network === "object" ? sb.network : {};
    const have = new Set(sb.network.allowedDomains || []);
    const add = hosts.filter((h) => !have.has(h));
    if (add.length) {
      sb.network.allowedDomains = [...(sb.network.allowedDomains || []), ...add];
      changes.push(`sandbox.network.allowedDomains: ${add.join(", ")} — the hosts these skills declare; shell commands reach no other host without asking`);
    }
  } else if (!alreadyOn) notes.push("these skills declare no network hosts, so shell commands reach none without asking");
  if ((sb.excludedCommands || []).length)
    notes.push(`this file's sandbox.excludedCommands (${sb.excludedCommands.join(", ")}) still run outside the sandbox`);
  notes.push('the sandbox covers shell commands only: Claude Code\'s file tools, web tools, MCP servers and hooks follow permission rules instead. ' +
             'To keep these skills off the web entirely, add "permissions": {"deny": ["WebFetch", "WebSearch"]} to this file.');
  return { uncontainable, hosts, changes, notes, next, changed: JSON.stringify(next) !== before };
}

/* Is a project already contained (strict sandbox on in its own settings)? For inventory and
   for a policy that requires containment. */
function contained(files) { return strictIn(readSettings(files.local)) || strictIn(readSettings(files.project)); }

module.exports = { containmentPlan, contained, load, check, prepare, audit, verifyAudit, verifyMirror, sourceKey, tilde, SEVERITY };

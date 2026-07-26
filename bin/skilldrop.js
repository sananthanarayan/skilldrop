#!/usr/bin/env node
/* skilldrop — install portable AI-agent skills into Claude Code, Cursor, Kiro,
 * or any directory, from the bundled catalog or any third-party catalog
 * (--from <path | git-url[#ref]>). Zero dependencies; copy-only, never executes
 * catalog content at install time.
 * Design: skilldrop-cli-design/skilldrop-cli-design.md
 * Scope:  docs/rfcs/0002-skilldrop-cli.md, docs/rfcs/0003-third-party-catalogs.md
 */
"use strict";
const fs = require("fs");
const path = require("path");
const os = require("os");
const { execFileSync } = require("child_process");

const ROOT = path.resolve(__dirname, "..");
const LEDGER = ".skilldrop.json";
const BUNDLED = "bundled";
// Neutral hook vocabulary (RFC-0006). Kept in sync with validate.py's HOOK_EVENTS.
const HOOK_EVENTS = ["session-start", "pre-commit-review", "on-demand"];

const HELP = `skilldrop — portable AI-agent skills for Claude Code, Cursor, Kiro, and more

Usage:
  skilldrop list [--from <src>]           all skills in a catalog (name, version, tier)
  skilldrop info <skill> [--from <src>]   description, related, packs, deps
  skilldrop packs [--from <src>]          role-based packs
  skilldrop agents [--from <src>]         reviewer subagents in a catalog
  skilldrop install <skill...>            install skills (default: Claude Code, user scope)
  skilldrop install --pack <name>         install a whole pack
  skilldrop install --all                 install every skill in the catalog
  skilldrop install --agent <name...>     install reviewer subagents (RFC-0012)
  skilldrop update                        re-copy installed skills whose version changed
  skilldrop outdated                      show installed vs current versions, change nothing
  skilldrop uninstall <skill...>          remove skills (and wiring files this tool wrote)
  skilldrop uninstall --agent <name...>   remove subagents
  skilldrop validate [--from <src>]       structural check of a catalog (for catalog authors)

Catalogs:
  (default)          the catalog bundled with this package
  --from <dir>       any local directory shaped like skills/<name>/{SKILL.md,manifest.json}
  --from <git-url>   any git repo with that shape; append #<branch-or-tag> to pin

Install/update/uninstall targets (pick one):
  (default)          ~/.claude/skills           Claude Code, user scope
  --project          ./.claude/skills           Claude Code + GitHub Copilot CLI, project scope
  --ide cursor       ./.cursor/skills           + writes .cursor/rules/<skill>.mdc
  --ide kiro         ./.kiro/skills             Kiro IDE + Kiro CLI (discovered natively)
  --dest <dir>       any directory              e.g. .agents/skills (Codex, Copilot CLI),
                                                .github/skills (Copilot), Continue / Cline / Aider

Options:
  --agent            operate on subagents instead of skills. Plain-copy targets only:
                     Claude Code (~/.claude/agents, --project for repo scope) or --dest.
                     Copilot/Kiro/Codex need a projection — see agents/README.md.
  --with-related     also install each skill's related companions (one level)
  --with-hooks       also wire any hooks a skill declares (RFC-0006) — git pre-commit
                     reminders and Claude Code session-start context; degrades where the
                     target has no hook mechanism. Off by default so installs never touch
                     your git repo or settings unasked.
`;

function die(msg) { console.error("error: " + msg); process.exit(1); }
function readJSON(p) { return JSON.parse(fs.readFileSync(p, "utf8")); }

function parseArgs(argv) {
  const out = { _: [], flags: {} };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--pack" || a === "--ide" || a === "--dest" || a === "--from") out.flags[a.slice(2)] = argv[++i];
    else if (a.startsWith("--")) out.flags[a.slice(2)] = true;
    else out._.push(a);
  }
  return out;
}

/* ---------- catalogs ---------- */

const catalogCache = {};
function resolveCatalog(source) {
  const key = source || BUNDLED;
  if (catalogCache[key]) return catalogCache[key];
  let dir;
  if (!source) dir = ROOT;
  else if (fs.existsSync(source)) dir = path.resolve(source);
  else {
    const [url, ref] = source.split("#");
    dir = fs.mkdtempSync(path.join(os.tmpdir(), "skilldrop-cat-"));
    try {
      execFileSync("git", ["clone", "--depth", "1", ...(ref ? ["--branch", ref] : []), url, dir], { stdio: ["ignore", "ignore", "pipe"] });
    } catch (e) {
      die(`could not fetch catalog '${source}' — not a local path, and git clone failed`);
    }
  }
  const skillsDir = path.join(dir, "skills");
  if (!fs.existsSync(skillsDir)) die(`'${source || dir}' is not a skilldrop catalog — no skills/ directory`);
  return (catalogCache[key] = { dir, skillsDir, source: source || BUNDLED });
}
function skillsIn(cat) {
  return fs.readdirSync(cat.skillsDir).filter((d) => fs.statSync(path.join(cat.skillsDir, d)).isDirectory()).sort();
}
function manifestOf(cat, s) { return readJSON(path.join(cat.skillsDir, s, "manifest.json")); }

/* Agents (RFC-0012): single markdown files, frontmatter is already Claude Code's format.
   Optional in a catalog — a third-party catalog with no agents/ is still valid. */
function agentsIn(cat) {
  const d = path.join(cat.dir, "agents");
  if (!fs.existsSync(d)) return [];
  return fs.readdirSync(d).filter((f) => f.endsWith(".md") && f !== "README.md").map((f) => f.slice(0, -3)).sort();
}
function agentPath(cat, a) { return path.join(cat.dir, "agents", `${a}.md`); }
function agentMeta(cat, a) {
  const fm = (fs.readFileSync(agentPath(cat, a), "utf8").split("---")[1] || "");
  const get = (k) => { const m = fm.match(new RegExp("^" + k + ":\\s*(.+)$", "m")); return m ? m[1].trim() : ""; };
  return { name: get("name"), description: get("description"), tools: get("tools"), model: get("model") };
}

/* Same gate the skills get, applied to agents before anything is copied. */
function checkAgent(cat, a) {
  const problems = [];
  if (!fs.existsSync(agentPath(cat, a))) return [`agents/${a}.md missing`];
  const m = agentMeta(cat, a);
  if (m.name !== a) problems.push(`frontmatter name '${m.name}' != filename '${a}'`);
  if (!m.description) problems.push("frontmatter missing description");
  return problems;
}
function packsOf(cat) {
  const p = path.join(cat.dir, "packs.json");
  return fs.existsSync(p) ? readJSON(p).packs : null;
}

/* Structural gate (RFC-0003): a skill must pass before it is copied anywhere. */
function checkSkill(cat, s) {
  const problems = [];
  const dir = path.join(cat.skillsDir, s);
  if (!fs.existsSync(path.join(dir, "SKILL.md"))) problems.push("SKILL.md missing");
  let m = null;
  try { m = manifestOf(cat, s); } catch (e) { problems.push("manifest.json missing or invalid JSON"); }
  if (m) {
    if (m.name !== s) problems.push(`manifest name '${m.name}' != folder '${s}'`);
    if (!m.description) problems.push("manifest missing description");
    if (!m.version) problems.push("manifest missing version");
    if (!m.model || !m.model.tier) problems.push("manifest missing model.tier");
    const fmName = (() => {
      try {
        const fm = fs.readFileSync(path.join(dir, "SKILL.md"), "utf8").split("---")[1] || "";
        const match = fm.match(/^name:\s*(\S+)/m);
        return match && match[1];
      } catch (e) { return null; }
    })();
    if (fmName && fmName !== s) problems.push(`SKILL.md frontmatter name '${fmName}' != folder '${s}'`);
  }
  return problems;
}
function gate(cat, names) {
  let bad = 0;
  for (const s of names) {
    const problems = checkSkill(cat, s);
    for (const p of problems) console.error(`refused ${s}: ${p}`);
    if (problems.length) bad++;
  }
  if (bad) die(`${bad} skill(s) failed the structural check — nothing was installed`);
}

/* ---------- install targets & ledger ---------- */

function target(flags) {
  if (flags.dest) return { dest: path.resolve(flags.dest), ide: "generic" };
  const ide = flags.ide || "claude";
  if (ide === "claude")
    return flags.project
      ? { dest: path.resolve(".claude", "skills"), ide }
      : { dest: path.join(os.homedir(), ".claude", "skills"), ide };
  if (ide === "cursor") return { dest: path.resolve(".cursor", "skills"), ide };
  if (ide === "kiro") return { dest: path.resolve(".kiro", "skills"), ide };
  die(`unknown --ide '${ide}' (claude | cursor | kiro; use --dest for anything else)`);
}

/* Only plain-copy targets ship in RFC-0012. Everything else needs a projection the
   install-target model (RFC-0010) has not settled — so say so instead of guessing a path. */
const AGENT_MANUAL = {
  copilot: ".github/agents/<name>.agent.md (rename needed)",
  kiro: ".kiro/agents/<name>.json (JSON wrapper around a file:// prompt)",
  cursor: "a custom mode — Cursor has no agent file format",
};
function agentTarget(flags) {
  if (flags.dest) return { dest: path.resolve(flags.dest), ide: "generic" };
  const ide = flags.ide || "claude";
  if (ide === "claude")
    return flags.project
      ? { dest: path.resolve(".claude", "agents"), ide }
      : { dest: path.join(os.homedir(), ".claude", "agents"), ide };
  const hint = AGENT_MANUAL[ide];
  die(`--agent has no plain-copy target for '${ide}'${hint ? ` — it needs ${hint}` : ""}.\n` +
      `       Copy it by hand (see agents/README.md), or use --dest <dir>. Tracked in RFC-0012.`);
}

function ledger(dest) {
  const p = path.join(dest, LEDGER);
  return { path: p, data: fs.existsSync(p) ? readJSON(p) : {} };
}
function saveLedger(l) { fs.writeFileSync(l.path, JSON.stringify(l.data, null, 2) + "\n"); }
/* Ledger values: {version, source}; legacy plain strings mean a bundled install. */
function lver(v) { return typeof v === "string" ? v : v.version; }
function lsrc(v) { return typeof v === "string" ? BUNDLED : v.source || BUNDLED; }

/* Wiring = the pointer file a target needs to *find* a skill.
   Cursor needs one: .cursor/skills/ is not a discovery path, so the .mdc rule is what
   makes the skill reachable (and it carries alwaysApply:false, so it stays inert until matched).
   Kiro no longer does: Kiro discovers .kiro/skills/ natively (Agent Skills, 2026-02-05), and a
   steering file with no frontmatter is always-included — so the old shim pinned one description
   per installed skill into every session's context to point at a folder Kiro already reads.
   wiringPath still resolves the Kiro path so uninstall and install can clean up legacy shims. */
const KIRO_SHIM_PREFIX = "When the user requests the following, defer to the instructions in .kiro/skills/";

function wiringPath(ide, dest, s) {
  const base = path.dirname(dest); // .cursor/ or .kiro/
  if (ide === "cursor") return path.join(base, "rules", `${s}.mdc`);
  if (ide === "kiro") return path.join(base, "steering", `${s}.md`);
  return null;
}
function writeWiring(ide, dest, s, desc) {
  if (ide === "kiro") return clearKiroShim(dest, s);
  const p = wiringPath(ide, dest, s);
  if (!p) return null;
  fs.mkdirSync(path.dirname(p), { recursive: true });
  fs.writeFileSync(p, `---\ndescription: ${desc.replace(/\n/g, " ")}\nglobs:\nalwaysApply: false\n---\nFollow the instructions in .cursor/skills/${s}/SKILL.md when the user requests this task.\n`);
  return null;
}
/* Remove a steering file this CLI wrote in an earlier version, so upgrading drops the context
   leak. Content-matched on purpose: a hand-written .kiro/steering/<skill>.md is the user's file
   and is left alone (with a note) rather than deleted. */
function clearKiroShim(dest, s) {
  const p = wiringPath("kiro", dest, s);
  if (!fs.existsSync(p)) return null;
  let body = "";
  try { body = fs.readFileSync(p, "utf8"); } catch (e) { return null; }
  if (!body.startsWith(KIRO_SHIM_PREFIX))
    return `  kept ${path.relative(process.cwd(), p)} — not written by skilldrop, left for you to review`;
  fs.rmSync(p, { force: true });
  return `  removed stale steering shim ${path.relative(process.cwd(), p)} — Kiro discovers .kiro/skills/ natively`;
}

/* ---------- hooks (RFC-0006: emit per target, degrade where unsupported) ---------- */

function gitRoot(startDir) {
  let d = path.resolve(startDir);
  for (;;) {
    if (fs.existsSync(path.join(d, ".git"))) return d;
    const up = path.dirname(d);
    if (up === d) return null;
    d = up;
  }
}

// Append an idempotent, marker-fenced reminder to .git/hooks/pre-commit. IDE-agnostic.
function writeGitPreCommitHook(root, skill, hook) {
  const p = path.join(root, ".git", "hooks", "pre-commit");
  const marker = `skilldrop-hook:${skill}:pre-commit-review`;
  let body = fs.existsSync(p) ? fs.readFileSync(p, "utf8") : "";
  if (!body.startsWith("#!")) body = "#!/bin/sh\n" + body;
  if (body.includes(marker)) return p; // already wired
  const line = `echo "skilldrop: run /${hook.action} on your staged changes before committing — ${hook.description}"`;
  body += `\n# >>> ${marker} >>>\n${line}\n# <<< ${marker} <<<\n`;
  fs.mkdirSync(path.dirname(p), { recursive: true });
  fs.writeFileSync(p, body);
  fs.chmodSync(p, 0o755);
  return p;
}

// Merge a SessionStart command into Claude Code settings.json. Returns the path,
// or null if the file exists but is malformed (we never clobber unparseable JSON).
function writeClaudeSessionHook(settingsPath, skill, hook) {
  let data = {};
  if (fs.existsSync(settingsPath)) {
    try { data = JSON.parse(fs.readFileSync(settingsPath, "utf8")); }
    catch (e) { return null; }
  }
  data.hooks = data.hooks || {};
  data.hooks.SessionStart = data.hooks.SessionStart || [];
  const marker = `skilldrop-hook:${skill}:session-start`;
  if (!JSON.stringify(data.hooks.SessionStart).includes(marker)) {
    const cmd = `echo "skilldrop: /${hook.action} is available — ${hook.description}" # ${marker}`;
    data.hooks.SessionStart.push({ hooks: [{ type: "command", command: cmd }] });
    fs.mkdirSync(path.dirname(settingsPath), { recursive: true });
    fs.writeFileSync(settingsPath, JSON.stringify(data, null, 2) + "\n");
  }
  return settingsPath;
}

// Wire one skill's declared hooks; returns human-readable status lines.
function emitHooks(cat, skill, dest, ide) {
  let hooks = [];
  try { hooks = manifestOf(cat, skill).hooks || []; } catch (e) { return []; }
  const lines = [];
  for (const h of hooks) {
    if (h.event === "pre-commit-review") {
      const root = gitRoot(process.cwd());
      if (root) lines.push(`  ${skill}: pre-commit reminder -> ${path.join(root, ".git/hooks/pre-commit")}`);
      else lines.push(`  ${skill}: pre-commit-review skipped — no git repo at ${process.cwd()}`);
      if (root) writeGitPreCommitHook(root, skill, h);
    } else if (h.event === "session-start") {
      if (ide === "claude") {
        const sp = path.join(path.dirname(dest), "settings.json");
        const written = writeClaudeSessionHook(sp, skill, h);
        lines.push(written ? `  ${skill}: session-start context -> ${sp}`
                           : `  ${skill}: session-start skipped — ${sp} is not valid JSON`);
      } else {
        lines.push(`  ${skill}: session-start skipped — no hook mechanism for ${ide}`);
      }
    } else if (h.event === "on-demand") {
      lines.push(`  ${skill}: on-demand — invoke /${h.action} manually (no artifact needed)`);
    }
  }
  return lines;
}

function removeHooksFor(skill, dest, ide) {
  const root = gitRoot(process.cwd());
  if (root) {
    const p = path.join(root, ".git", "hooks", "pre-commit");
    if (fs.existsSync(p)) {
      const body = fs.readFileSync(p, "utf8");
      const re = new RegExp(`\\n?# >>> skilldrop-hook:${skill}:[^\\n]* >>>[\\s\\S]*?# <<< skilldrop-hook:${skill}:[^\\n]* <<<\\n?`, "g");
      const next = body.replace(re, "\n");
      if (next !== body) fs.writeFileSync(p, next);
    }
  }
  if (ide === "claude") {
    const sp = path.join(path.dirname(dest), "settings.json");
    if (fs.existsSync(sp)) {
      try {
        const data = JSON.parse(fs.readFileSync(sp, "utf8"));
        const arr = data.hooks && data.hooks.SessionStart;
        if (Array.isArray(arr)) {
          const kept = arr.filter((e) => !JSON.stringify(e).includes(`skilldrop-hook:${skill}:`));
          if (kept.length !== arr.length) { data.hooks.SessionStart = kept; fs.writeFileSync(sp, JSON.stringify(data, null, 2) + "\n"); }
        }
      } catch (e) { /* leave malformed settings untouched */ }
    }
  }
}

/* ---------- commands ---------- */

function expandNames(args, cat) {
  if (args.flags.all) return skillsIn(cat);
  if (args.flags.pack) {
    const ps = packsOf(cat);
    if (!ps) die(`catalog '${cat.source}' has no packs.json — install skills by name`);
    const p = ps[args.flags.pack];
    if (!p) die(`unknown pack '${args.flags.pack}' in catalog '${cat.source}'`);
    return p.skills.slice();
  }
  if (!args._.length) die("nothing to install — pass skill names, --pack <name>, or --all");
  for (const s of args._) if (!fs.existsSync(path.join(cat.skillsDir, s))) die(`unknown skill '${s}' in catalog '${cat.source}'`);
  return args._.slice();
}

function copyOne(cat, s, dest, ide, l, notes) {
  const m = manifestOf(cat, s);
  fs.cpSync(path.join(cat.skillsDir, s), path.join(dest, s), { recursive: true });
  const note = writeWiring(ide, dest, s, m.description);
  if (note && notes) notes.push(note);
  l.data[s] = { version: m.version, source: cat.source };
  return m;
}

function install(args) {
  if (args.flags.agent) return installAgents(args);
  const cat = resolveCatalog(args.flags.from);
  let names = expandNames(args, cat);
  if (args.flags["with-related"]) {
    const seen = new Set(names);
    for (const s of names.slice()) {
      let related = [];
      try { related = manifestOf(cat, s).related || []; } catch (e) { /* gated below */ }
      for (const r of related) if (!seen.has(r) && fs.existsSync(path.join(cat.skillsDir, r))) { seen.add(r); names.push(r); }
    }
  }
  gate(cat, names);
  const { dest, ide } = target(args.flags);
  fs.mkdirSync(dest, { recursive: true });
  const l = ledger(dest);
  const pipDeps = [], suggestions = new Set(), notes = [];
  for (const s of names) {
    const m = copyOne(cat, s, dest, ide, l, notes);
    if (fs.existsSync(path.join(cat.skillsDir, s, "requirements.txt"))) pipDeps.push(s);
    for (const r of m.related || []) if (!names.includes(r) && !l.data[r]) suggestions.add(r);
    console.log(`installed ${s}@${m.version} -> ${dest}`);
  }
  saveLedger(l);
  console.log(`\n${names.length} skill(s) installed (${ide}).`);
  if (notes.length) console.log(`\nCleanup:\n${notes.join("\n")}`);

  const withHooks = names.filter((s) => { try { return (manifestOf(cat, s).hooks || []).length; } catch (e) { return false; } });
  if (withHooks.length && args.flags["with-hooks"]) {
    const lines = withHooks.flatMap((s) => emitHooks(cat, s, dest, ide));
    console.log(`\nHooks wired (RFC-0006):\n${lines.join("\n")}`);
    if (cat.source !== BUNDLED)
      console.log(`  NOTE: these hooks run commands from third-party catalog '${cat.source}' — read them before trusting them.`);
    console.log(`  Undo any of these with: skilldrop uninstall <skill> ${ide === "claude" ? "" : "--ide " + ide}`.trimEnd());
  } else if (withHooks.length) {
    console.log(`\n${withHooks.join(", ")} declare hooks — re-run with --with-hooks to wire them (git pre-commit reminders / session-start context).`);
  }

  if (cat.source !== BUNDLED)
    console.log(`\nWARNING: third-party catalog '${cat.source}'. Skills are instructions your AI agent will follow — review each installed SKILL.md under ${dest} before first use. Install copied files only; nothing was executed.`);
  if (ide === "generic")
    console.log("wiring: attach each skill's SKILL.md to your agent (Continue/Cline: @file, Aider: /add, Codex: reference it from AGENTS.md) — see the repo README's per-IDE steps.");
  for (const s of pipDeps)
    console.log(`deps: ${s} needs Python packages — run: cd ${path.join(dest, s)} && python3 -m pip install -r requirements.txt`);
  if (suggestions.size)
    console.log(`related (not installed): ${[...suggestions].sort().join(", ")} — add --with-related or install by name.`);
}

function installedRows(flags) {
  const { dest, ide } = target(flags);
  const l = ledger(dest);
  const rows = Object.keys(l.data).sort().map((s) => {
    const src = lsrc(l.data[s]);
    let current = null, cat = null;
    try {
      cat = resolveCatalog(src === BUNDLED ? undefined : src);
      if (fs.existsSync(path.join(cat.skillsDir, s))) current = manifestOf(cat, s).version;
    } catch (e) { /* unreachable source: current stays null */ }
    return { s, src, cat, installed: lver(l.data[s]), current };
  });
  return { dest, ide, l, rows };
}

function update(args) {
  const { dest, ide, l, rows } = installedRows(args.flags);
  if (!rows.length) return console.log(`nothing installed at ${dest}`);
  let n = 0;
  for (const r of rows) {
    if (!r.current) { console.log(`skip ${r.s}: source '${r.src}' unreachable or skill gone from it`); continue; }
    if (r.current === r.installed) continue;
    const problems = checkSkill(r.cat, r.s);
    if (problems.length) { console.log(`skip ${r.s}: fails structural check in '${r.src}' (${problems[0]})`); continue; }
    copyOne(r.cat, r.s, dest, ide, l);
    console.log(`updated ${r.s} ${r.installed} -> ${r.current} (${r.src})`);
    n++;
  }
  saveLedger(l);
  console.log(n ? `\n${n} skill(s) updated.` : "everything up to date.");
}

function outdated(args) {
  const { dest, rows } = installedRows(args.flags);
  if (!rows.length) return console.log(`nothing installed at ${dest}`);
  const stale = rows.filter((r) => r.current && r.current !== r.installed);
  for (const r of stale) console.log(`${r.s}: installed ${r.installed}, current ${r.current} (${r.src})`);
  console.log(stale.length ? `\n${stale.length} outdated — run: skilldrop update` : "everything up to date.");
}

function uninstall(args) {
  if (args.flags.agent) return uninstallAgents(args);
  if (!args._.length) die("pass skill names to uninstall");
  const { dest, ide } = target(args.flags);
  const l = ledger(dest);
  for (const s of args._) {
    fs.rmSync(path.join(dest, s), { recursive: true, force: true });
    const w = wiringPath(ide, dest, s);
    if (w) fs.rmSync(w, { force: true });
    removeHooksFor(s, dest, ide);
    delete l.data[s];
    console.log(`removed ${s} from ${dest}`);
  }
  saveLedger(l);
}

function listAgents(args) {
  const cat = resolveCatalog(args.flags.from);
  const names = agentsIn(cat);
  if (!names.length) return console.log(`catalog '${cat.source}' ships no agents.`);
  const w = Math.max(...names.map((n) => n.length));
  for (const a of names) {
    const m = agentMeta(cat, a);
    console.log(`${a.padEnd(w)}  ${m.description}`);
  }
  console.log(`\n${names.length} agent(s). Install one: skilldrop install --agent <name>`);
}

function installAgents(args) {
  const cat = resolveCatalog(args.flags.from);
  const available = agentsIn(cat);
  if (!available.length) die(`catalog '${cat.source}' ships no agents`);
  const names = args._.length ? args._.slice() : (args.flags.all ? available : []);
  if (!names.length) die("nothing to install — pass agent names, or --all");
  for (const a of names) if (!available.includes(a)) die(`unknown agent '${a}' in catalog '${cat.source}'`);

  let bad = 0;
  for (const a of names) {
    const problems = checkAgent(cat, a);
    for (const pr of problems) console.error(`refused ${a}: ${pr}`);
    if (problems.length) bad++;
  }
  if (bad) die(`${bad} agent(s) failed the structural check — nothing was installed`);

  const { dest, ide } = agentTarget(args.flags);
  fs.mkdirSync(dest, { recursive: true });
  const l = ledger(dest);
  for (const a of names) {
    fs.copyFileSync(agentPath(cat, a), path.join(dest, `${a}.md`));
    l.data[a] = { version: null, source: cat.source }; // agents carry no version yet (RFC-0012)
    console.log(`installed ${a} -> ${dest}`);
  }
  saveLedger(l);
  console.log(`\n${names.length} agent(s) installed (${ide}).`);
  if (ide === "claude") console.log("Delegate by name, e.g. \"use the devils-advocate agent on this diff\".");
  if (cat.source !== BUNDLED)
    console.log(`\nWARNING: third-party catalog '${cat.source}'. An agent is a system prompt your tool will adopt — read it before first use. Install copied files only; nothing was executed.`);
}

function uninstallAgents(args) {
  if (!args._.length) die("pass agent names to uninstall");
  const { dest } = agentTarget(args.flags);
  const l = ledger(dest);
  for (const a of args._) {
    fs.rmSync(path.join(dest, `${a}.md`), { force: true });
    delete l.data[a];
    console.log(`removed ${a} from ${dest}`);
  }
  saveLedger(l);
}

function list(args) {
  const cat = resolveCatalog(args.flags.from);
  const rows = skillsIn(cat).map((s) => {
    try { const m = manifestOf(cat, s); return [s, m.version || "?", (m.model && m.model.tier) || "?"]; }
    catch (e) { return [s, "?", "?"]; }
  });
  const w = Math.max(...rows.map((r) => r[0].length));
  for (const [s, v, t] of rows) console.log(`${s.padEnd(w)}  ${v}  ${t}`);
  console.log(`\n${rows.length} skills in catalog '${cat.source}'. Details: skilldrop info <skill>`);
}

function info(args) {
  const cat = resolveCatalog(args.flags.from);
  const s = args._[0] || die("pass a skill name");
  if (!fs.existsSync(path.join(cat.skillsDir, s))) die(`unknown skill '${s}' in catalog '${cat.source}'`);
  const m = manifestOf(cat, s);
  const ps = packsOf(cat) || {};
  const inPacks = Object.entries(ps).filter(([, p]) => p.skills.includes(s)).map(([n]) => n);
  console.log(`${m.name}@${m.version}  (tier: ${m.model && m.model.tier})\n\n${m.description}\n`);
  console.log(`catalog: ${cat.source}`);
  console.log(`packs:   ${inPacks.join(", ") || "-"}`);
  console.log(`related: ${(m.related || []).join(", ") || "-"}`);
  if (((m.deps || {}).pip || []).length || fs.existsSync(path.join(cat.skillsDir, s, "requirements.txt")))
    console.log("deps:    python (requirements.txt)");
  if (((m.env || {}).required || []).length) console.log(`env:     ${m.env.required.join(", ")} (required)`);
}

function listPacks(args) {
  const cat = resolveCatalog(args.flags.from);
  const ps = packsOf(cat);
  if (!ps) return console.log(`catalog '${cat.source}' defines no packs.`);
  const w = Math.max(...Object.keys(ps).map((n) => n.length));
  for (const [n, p] of Object.entries(ps))
    console.log(`${n.padEnd(w)}  (${p.skills.length} skills)  ${p.description}`);
  console.log("\nInstall one: skilldrop install --pack <name>");
}

function validateCmd(args) {
  const cat = resolveCatalog(args.flags.from);
  const names = skillsIn(cat);
  let bad = 0;
  for (const s of names) {
    const problems = checkSkill(cat, s);
    for (const p of problems) console.log(`FAIL ${s}: ${p}`);
    if (problems.length) bad++;
  }
  const ps = packsOf(cat);
  if (ps)
    for (const [n, p] of Object.entries(ps))
      for (const s of p.skills)
        if (!names.includes(s)) { console.log(`FAIL packs.json: pack '${n}' lists unknown skill '${s}'`); bad++; }
  if (bad) { console.log(`\n${bad} problem(s) in catalog '${cat.source}'.`); process.exit(1); }
  console.log(`OK: ${names.length} skills in catalog '${cat.source}' pass the structural check.`);
}

const args = parseArgs(process.argv.slice(2));
const cmd = args._.shift();
const commands = { list, info, packs: listPacks, agents: listAgents, install, update, outdated, uninstall, validate: validateCmd };
if (!cmd || cmd === "help" || args.flags.help) console.log(HELP);
else if (commands[cmd]) commands[cmd](args);
else die(`unknown command '${cmd}' — run: skilldrop help`);

#!/usr/bin/env node
/* skilldrop — install portable AI-agent skills into Claude Code, Cursor, Kiro,
 * or any directory, from the bundled catalog or any third-party catalog
 * (--from <path | git-url[#ref]>). Zero dependencies; copy-only, never executes
 * catalog content at install time.
 * Reads three catalog shapes: skilldrop pack folders (packs/<p>/pack.json + packs/<p>/skills/),
 * flat skilldrop (skills/ + packs.json), and agentbundle (packs/<p>/pack.toml + .apm/skills).
 * Design: skilldrop-cli-design/skilldrop-cli-design.md
 * Scope:  docs/rfcs/0002-skilldrop-cli.md, docs/rfcs/0003-third-party-catalogs.md,
 *         docs/rfcs/0014-agentbundle-interop.md (the agentbundle reader)
 */
"use strict";
const fs = require("fs");
const path = require("path");
const os = require("os");
const { execFileSync } = require("child_process");
const crypto = require("crypto");

const ROOT = path.resolve(__dirname, "..");
const LEDGER = ".skilldrop.json";
const BUNDLED = "bundled";
// Neutral hook vocabulary (RFC-0006). Kept in sync with validate.py's HOOK_EVENTS.
const HOOK_EVENTS = ["session-start", "pre-commit-review", "on-demand"];

// Panels (RFC-0020): a named bundle of reviewer subagents + the orchestrator skill that fires
// them in parallel. `install --panel <name>` installs the whole fleet in one command.
const PANELS = {
  review: {
    agents: ["devils-advocate", "security-reviewer", "code-quality"],
    skill: "pre-merge-review",
    blurb: "correctness + security + craft reviewers, fired in parallel by pre-merge-review",
  },
};

const HELP = `skilldrop — portable AI-agent skills for Claude Code, Cursor, Kiro, and more

Usage:
  skilldrop list [--from <src>]           all skills in a catalog (name, version, tier)
  skilldrop info <skill> [--from <src>]   description, related, packs, deps
  skilldrop info --pack <name>            a pack's skills, loops, and what to try first (RFC-0032)
  skilldrop packs [--from <src>]          role-based packs
  skilldrop agents [--from <src>]         reviewer subagents in a catalog
  skilldrop loops [--from <src>]          loops — sequenced stages over skills (RFC-0028)
  skilldrop install <skill...>            install skills (default: Claude Code, user scope)
  skilldrop install --pack <name>         install a whole pack
  skilldrop install --profile <name>      install a named bundle of packs, agents, and loops
  skilldrop profiles [--from <src>]       list available profiles
  skilldrop install --all                 install every skill in the catalog
  skilldrop install --agent <name...>     install reviewer subagents (RFC-0012)
  skilldrop install --loop <name...>      install loops + the stage skills they sequence
                                          (--no-skills for the loop alone) (RFC-0028)
  skilldrop install --panel review        install the review panel — the 3 reviewer subagents +
                                          the pre-merge-review orchestrator that fires them (RFC-0020)
  skilldrop update [--force] [--changed]  re-copy installed skills whose version changed; files
                                          you edited are kept and the new copy lands beside them
                                          as <file>.upstream (--force overwrites) (RFC-0032).
                                          Files changed upstream under the same version are named,
                                          not taken, unless you add --changed (RFC-0039)
  skilldrop outdated                      show installed vs current versions, change nothing
  skilldrop diff <skill> [--stat]         what differs between your installed copy and the catalog's —
                                          your edits, upstream changes, or both
  skilldrop doctor                        check a target against its ledger: missing folders, leftover
                                          .upstream files, stale wiring and hooks. Changes nothing.
  skilldrop uninstall <skill...>          remove skills (and wiring files this tool wrote)
  skilldrop uninstall --agent <name...>   remove subagents
  skilldrop uninstall --loop <name...>    remove loops (stage skills are left in place)
  skilldrop validate [--from <src>]       structural check of a catalog (for catalog authors)
  skilldrop scan [<skill...>] [--from <src>]  supply-chain scan — flag network/exec/credential
                                          patterns in scripts and injection-shaped instructions
                                          in SKILL.md before you trust a catalog (RFC-0022)
  skilldrop new-skill <name> --pack <p>   scaffold a skill in the catalog you're in (for catalog authors;
                                          --tier light|standard|heavy, default standard)
  skilldrop loop-stats [<file>] [--days N]  summarise the opt-in loop run log (SKILLDROP_LOOP_LOG):
                                          which gates pass first time, loop back, or block. Local only.
  skilldrop init-catalogue <dir> [--pack <name>]  start a private catalogue for your team's skills
  skilldrop package <dir> [--pack a,b] [--skills x,y] [--agents]  copy a vetted subset of a catalogue
                                          into a standalone one to host internally (writes MIRROR.json)
  skilldrop --version                     print the CLI version
  skilldrop bootstrap                     add the skilldrop marketplace to ~/.claude/settings.json
                                          (idempotent — safe to run in onboarding scripts)

Catalogs:
  (default)          the catalog bundled with this package
  --from <dir|url>   a skilldrop catalog (packs/<pack>/skills/<name>/ or flat skills/<name>/) OR
                     an agentbundle one (packs/<pack>/.apm/skills/<name>/SKILL.md); a git URL
                     works for either. Append #<commit-sha> to pin exactly (a branch or tag can
                     move after you review it); installs record the commit they got

Install/update/uninstall targets (pick one):
  (default)          ~/.claude/skills           Claude Code, user scope
  --project          ./.claude/skills           Claude Code + GitHub Copilot CLI, project scope
  --ide cursor       ./.cursor/skills           + writes .cursor/rules/<skill>.mdc
  --ide kiro         ./.kiro/skills             Kiro IDE + Kiro CLI (discovered natively)
  --ide codex        ~/.codex/skills            Codex (--project: ./.agents/skills)
  --ide antigravity  ~/.gemini/antigravity-cli/skills   Antigravity CLI (--project: ./.agents/skills)
  --ide copilot      ~/.copilot/skills          GitHub Copilot (--project: ./.github/skills)
  --dest <dir>       any directory              e.g. Continue / Cline / Aider
  --local            project scope, hidden from git via .git/info/exclude — try skills in a
                     repo you don't own without touching its tracked files or .gitignore

Options:
  --dry-run          install | update | uninstall | new-skill: print what would change, change nothing
  --yes              skip the confirmation uninstall and update --force ask for at a terminal
                     (scripts and CI are never asked)
  --agent            operate on subagents instead of skills. Targets:
                       (default)      ~/.claude/agents      Claude Code (--project for repo scope)
                       --ide kiro     ./.kiro/agents        generated JSON, tools mapped
                       --ide copilot  ./.github/agents      <name>.agent.md
                       --ide codex    ~/.codex/agents       generated TOML (--project for repo)
                       --ide antigravity  ~/.gemini/config/agents  markdown, subagent: true
                       --dest <dir>   any directory         copied as-is
                     Cursor has no agent format — use a custom mode (agents/README.md).
  --json             machine-readable output for list | info | packs | agents | outdated | doctor —
                     one JSON object on stdout, nothing else (for agents, scripts, CI)
  --with-related     also install each skill's related companions (one level)
  --with-hooks       also wire any hooks a skill declares (RFC-0006) — git pre-commit
                     reminders and Claude Code session-start context; degrades where the
                     target has no hook mechanism. Off by default so installs never touch
                     your git repo or settings unasked.
`;

function die(msg) { console.error("error: " + msg); process.exit(1); }
function readJSON(p) { return JSON.parse(fs.readFileSync(p, "utf8")); }

/* --json (RFC-0021): the read commands emit one machine-readable object on stdout and nothing
   else, so an agent or script can consume them without scraping aligned columns. Human output is
   unchanged by default — this is additive. Errors still go to stderr and exit non-zero. */
function emitJSON(obj) { console.log(JSON.stringify(obj, null, 2)); }

function parseArgs(argv) {
  const out = { _: [], flags: {} };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--pack" || a === "--ide" || a === "--dest" || a === "--from" || a === "--panel" || a === "--profile" || a === "--tier" || a === "--skills" || a === "--days") out.flags[a.slice(2)] = argv[++i];
    else if (a.startsWith("--")) out.flags[a.slice(2)] = true;
    else out._.push(a);
  }
  return out;
}

/* ---------- catalogs ----------
   Three on-disk shapes are read (RFC-0003, RFC-0014, RFC-0034):
     "packs"     — skilldrop's own layout since RFC-0034: packs/<pack>/{pack.json,
                   skills/<name>/{SKILL.md,manifest.json}, loops/<name>/} + catalogue.json
     "skilldrop" — flat skills/<name>/{SKILL.md,manifest.json} + optional packs.json; what
                   skilldrop shipped before RFC-0034, and what most third-party catalogs use
     "apm"       — agentbundle (agent-ready-repo): packs/<pack>/{pack.toml,
                   .apm/skills/<name>/SKILL.md, .apm/agents/<name>.md}
   The apm reader normalizes into the same accessors the native path uses — skills keyed by
   folder name, a per-skill manifest synthesized from the SKILL.md frontmatter + the pack.toml
   version, each pack.toml's [pack] table a virtual pack — so `--from git+https://…/agent-ready-repo`
   installs his packs through this same CLI. Skill accessors: skillsIn / skillDir / skillExists /
   manifestOf; never touch cat.skillsDir directly (it exists only on the flat skilldrop shape). */

const catalogCache = {};
/* Commit pinning (RFC-0039, OWASP AST02/AST07). A tag or branch can be moved to point at
   different code after you reviewed it; a commit SHA cannot. `--from <url>#<sha>` fetches
   exactly that commit, and every install records the commit it actually got, so the ledger
   says what is on disk and an unpinned install can tell you how to pin it. */
const SHA_RE = /^[0-9a-f]{7,40}$/i;
function gitHead(dir) {
  try {
    return execFileSync("git", ["rev-parse", "HEAD"], { cwd: dir, encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] }).trim() || null;
  } catch (e) { return null; }
}
function splitSource(source) {
  const i = source.lastIndexOf("#");
  return i > 0 ? [source.slice(0, i), source.slice(i + 1)] : [source, ""];
}
function isPinned(source) { return !!source && SHA_RE.test(splitSource(source)[1]); }

function fetchCatalog(source) {
  const [url, ref] = splitSource(source);
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "skilldrop-cat-"));
  const git = (args, cwd) => execFileSync("git", args, { cwd, stdio: ["ignore", "ignore", "pipe"] });
  try {
    if (SHA_RE.test(ref)) {
      // `git clone --branch` takes branches and tags, not commits: fetch the commit itself.
      git(["init", "-q"], dir);
      git(["remote", "add", "origin", url], dir);
      let direct = ref.length === 40;
      if (direct) {
        try { git(["fetch", "-q", "--depth", "1", "origin", ref], dir); }
        catch (e) { direct = false; }  // a host that won't serve a commit by itself
      }
      if (!direct) git(["fetch", "-q", "origin", "+refs/heads/*:refs/remotes/origin/*", "+refs/tags/*:refs/tags/*"], dir);
      try { git(["checkout", "-q", direct ? "FETCH_HEAD" : ref], dir); }
      catch (e) { die(`catalog '${source}': commit ${ref} isn't in that repository (check the SHA, or that it was pushed)`); }
    } else {
      git(["clone", "-q", "--depth", "1", ...(ref ? ["--branch", ref] : []), url, dir]);
    }
  } catch (e) {
    die(`could not fetch catalog '${source}' — not a local path, and git ${SHA_RE.test(ref) ? "could not fetch that commit" : "clone failed"}`);
  }
  const head = gitHead(dir);
  if (SHA_RE.test(ref) && (!head || !head.startsWith(ref.toLowerCase())))
    die(`catalog '${source}' resolved to ${head || "nothing"}, not the pinned commit ${ref}`);
  return dir;
}

function resolveCatalog(source) {
  const key = source || BUNDLED;
  if (catalogCache[key]) return catalogCache[key];
  let dir;
  if (!source) dir = ROOT;
  else if (fs.existsSync(source)) dir = path.resolve(source);
  else dir = fetchCatalog(source);
  const src = source || BUNDLED;
  // The bundled catalog is versioned by the npm package; anything else by its git commit.
  const meta = { commit: source ? gitHead(dir) : null, pinned: isPinned(source) };
  const packsDir = path.join(dir, "packs");
  if (fs.existsSync(packsDir) && fs.readdirSync(packsDir).some((p) => fs.existsSync(path.join(packsDir, p, "pack.json"))))
    return (catalogCache[key] = Object.assign(readPacksCatalog(dir, src), meta));
  if (fs.existsSync(path.join(dir, "skills")))
    return (catalogCache[key] = Object.assign({ dir, source: src, shape: "skilldrop", skillsDir: path.join(dir, "skills") }, meta));
  if (fs.existsSync(path.join(dir, "packs")))
    return (catalogCache[key] = Object.assign(readApmCatalog(dir, src), meta));
  die(`'${src}' is not a catalog — expected packs/<pack>/pack.json, a skills/ directory, or packs/<pack>/pack.toml (agentbundle)`);
}

/* RFC-0034: membership is the folder. A skill is in a pack because it sits at
   packs/<pack>/skills/<name>/; catalogue.json only sets the order packs are listed in. */
function readPacksCatalog(dir, source) {
  const packsDir = path.join(dir, "packs");
  const children = (d, marker) => fs.existsSync(d)
    ? fs.readdirSync(d).filter((x) => fs.existsSync(path.join(d, x, marker))).sort() : [];
  const onDisk = children(packsDir, "pack.json");
  const idx = path.join(dir, "catalogue.json");
  const listed = fs.existsSync(idx) ? (readJSON(idx).packs || []).filter((p) => onDisk.includes(p)) : [];
  const order = [...listed, ...onDisk.filter((p) => !listed.includes(p))];
  const skillIndex = {}, loopIndex = {}, packsData = {};
  for (const pack of order) {
    const pdir = path.join(packsDir, pack);
    const skills = children(path.join(pdir, "skills"), "SKILL.md");
    const loops = children(path.join(pdir, "loops"), "loop.json");
    for (const s of skills) if (!skillIndex[s]) skillIndex[s] = { dir: path.join(pdir, "skills", s) };
    for (const l of loops) if (!loopIndex[l]) loopIndex[l] = path.join(pdir, "loops", l);
    packsData[pack] = Object.assign({}, readJSON(path.join(pdir, "pack.json")), { skills, loops });
  }
  return { dir, source, shape: "packs", skillIndex, loopIndex, packsData };
}

/* Minimal TOML read — the [pack] table's basic-string scalars (name, version, description).
   pack.toml is small and regular; a full TOML parser would be dead weight in a zero-dep CLI. */
function packMeta(tomlText) {
  const out = {};
  let inPack = false;
  for (const raw of tomlText.split(/\r?\n/)) {
    const t = raw.trim();
    if (t.startsWith("[")) { inPack = t === "[pack]"; continue; }
    if (!inPack || !t || t.startsWith("#")) continue;
    const m = t.match(/^([A-Za-z0-9_.-]+)\s*=\s*"((?:[^"\\]|\\.)*)"/);
    if (m) out[m[1]] = m[2].replace(/\\"/g, '"').replace(/\\\\/g, "\\");
  }
  return out;
}

/* SKILL.md frontmatter (agentskills.io: name optional, description carries the trigger). */
function frontmatter(mdPath) {
  let fm = "";
  try { fm = fs.readFileSync(mdPath, "utf8").split("---")[1] || ""; } catch (e) { return {}; }
  const get = (k) => { const m = fm.match(new RegExp("^" + k + ":\\s*(.+)$", "m")); return m ? m[1].trim() : ""; };
  return { name: get("name"), description: get("description") };
}

/* Read an agentbundle catalog into the native accessor shape. First-wins on a skill name
   (skilldrop's own generated catalogue duplicates a multi-pack skill into each pack — the
   flat skill list dedups, while packsData still lists it under every pack it belongs to). */
function readApmCatalog(dir, source) {
  const packsDir = path.join(dir, "packs");
  const skillIndex = {}, agentIndex = {}, packsData = {};
  for (const pack of fs.readdirSync(packsDir)) {
    const pdir = path.join(packsDir, pack);
    if (!fs.statSync(pdir).isDirectory()) continue;
    const ptoml = path.join(pdir, "pack.toml");
    const pm = fs.existsSync(ptoml) ? packMeta(fs.readFileSync(ptoml, "utf8")) : {};
    const version = pm.version || "0.0.0";
    const skills = [];
    const skillsRoot = path.join(pdir, ".apm", "skills");
    if (fs.existsSync(skillsRoot))
      for (const s of fs.readdirSync(skillsRoot)) {
        const sdir = path.join(skillsRoot, s);
        if (!fs.statSync(sdir).isDirectory()) continue;
        skills.push(s);
        if (!skillIndex[s])
          skillIndex[s] = { dir: sdir, manifest: {
            name: s, description: frontmatter(path.join(sdir, "SKILL.md")).description || "",
            version, related: [], tags: [],
            deps: { pip: [], npm: [] }, env: { required: [], optional: [] },
          } };
      }
    const agentsRoot = path.join(pdir, ".apm", "agents");
    if (fs.existsSync(agentsRoot))
      for (const f of fs.readdirSync(agentsRoot))
        if (f.endsWith(".md") && f !== "README.md") agentIndex[f.slice(0, -3)] = path.join(agentsRoot, f);
    packsData[pack] = { description: pm.description || "", skills };
  }
  return { dir, source, shape: "apm", skillIndex, agentIndex, packsData };
}

function skillsIn(cat) {
  if (cat.skillIndex) return Object.keys(cat.skillIndex).sort();
  return fs.readdirSync(cat.skillsDir).filter((d) => fs.statSync(path.join(cat.skillsDir, d)).isDirectory()).sort();
}
function skillDir(cat, s) {
  if (cat.skillIndex) return cat.skillIndex[s] && cat.skillIndex[s].dir;
  return path.join(cat.skillsDir, s);
}
// Skill names reach RegExp when unwiring hooks. skillExists() proves a directory exists; it
// does not prove the name is regex-safe, and a third-party catalog (RFC-0003) may name a
// skill anything a filesystem accepts. Escape before interpolating.
// Read a file if it is there. Checking existsSync first then reading is a race: the file can
// vanish in between and the read throws. Handle the absence, do not predict it.
function readIfPresent(p, absent = "") {
  try { return fs.readFileSync(p, "utf8"); }
  catch (e) { if (e.code === "ENOENT" || e.code === "ENOTDIR") return absent; throw e; }
}
function reEscape(s) { return String(s).replace(/[.*+?^${}()|[\]\\]/g, "\\$&"); }
function skillExists(cat, s) { const d = skillDir(cat, s); return !!d && fs.existsSync(d); }
function manifestOf(cat, s) {
  if (cat.shape === "apm") {
    if (!cat.skillIndex[s]) throw new Error(`no such skill '${s}'`);
    return cat.skillIndex[s].manifest;
  }
  return readJSON(path.join(skillDir(cat, s), "manifest.json"));
}

/* Agents (RFC-0012): single markdown files, frontmatter is already Claude Code's format.
   Optional in a catalog — a third-party catalog with no agents is still valid. */
function agentsIn(cat) {
  if (cat.shape === "apm") return Object.keys(cat.agentIndex).sort();
  const d = path.join(cat.dir, "agents");
  if (!fs.existsSync(d)) return [];
  return fs.readdirSync(d).filter((f) => f.endsWith(".md") && f !== "README.md").map((f) => f.slice(0, -3)).sort();
}
function agentPath(cat, a) {
  if (cat.shape === "apm") return cat.agentIndex[a];
  return path.join(cat.dir, "agents", `${a}.md`);
}
function agentMeta(cat, a) {
  const fm = (fs.readFileSync(agentPath(cat, a), "utf8").split("---")[1] || "");
  const get = (k) => { const m = fm.match(new RegExp("^" + k + ":\\s*(.+)$", "m")); return m ? m[1].trim() : ""; };
  return { name: get("name"), description: get("description"), tools: get("tools"), model: get("model") };
}

/* Same gate the skills get, applied to agents before anything is copied. */
function checkAgent(cat, a) {
  const problems = [];
  const p = agentPath(cat, a);
  if (!p || !fs.existsSync(p)) return [`agent '${a}' missing`];
  const m = agentMeta(cat, a);
  if (m.name !== a) problems.push(`frontmatter name '${m.name}' != filename '${a}'`);
  if (!m.description) problems.push("frontmatter missing description");
  return problems;
}
function packsOf(cat) {
  if (cat.packsData) return Object.keys(cat.packsData).length ? cat.packsData : null;
  const p = path.join(cat.dir, "packs.json");
  return fs.existsSync(p) ? readJSON(p).packs : null;
}
/* RFC-0033: a pack installs together with the packs it `requires` (in practice, core), so
   one --pack still delivers a role's whole toolkit now that shared skills have one home. */
function packMembers(ps, name, key) {
  const req = (ps[name].requires || []).filter((r) => ps[r]);
  const out = [];
  for (const n of [...req, name]) for (const x of ps[n][key] || []) if (!out.includes(x)) out.push(x);
  if (req.length) console.log(`pack '${name}' includes ${req.join(", ")}`);
  return out;
}
function profilesOf(cat) {
  const p = path.join(cat.dir, "profiles.json");
  return fs.existsSync(p) ? readJSON(p).profiles : null;
}

/* Structural gate (RFC-0003): a skill must pass before it is copied anywhere. */
function checkSkill(cat, s) {
  const problems = [];
  const dir = skillDir(cat, s);
  if (!dir || !fs.existsSync(path.join(dir, "SKILL.md"))) problems.push("SKILL.md missing");
  if (cat.shape === "apm") {
    // agentbundle skills carry name/description in SKILL.md frontmatter (agentskills.io);
    // version lives in pack.toml and there is no model tier — gate only the portable fields.
    if (!problems.length && !manifestOf(cat, s).description) problems.push("SKILL.md frontmatter missing description");
    return problems;
  }
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

/* ---------- supply-chain scan (RFC-0022) ----------
   A skill is instruction prose an agent will obey, and its scripts are code that runs on the
   user's machine — so installing a third-party catalog is a supply-chain event. Anthropic's own
   Skills guidance says to audit a skill's files for "unexpected network calls, file access
   patterns, or operations that don't match the Skill's stated purpose"; this automates that first
   pass. It is a HEURISTIC that reports — it never blocks and never replaces reading the skill.

   Two rule sets, deliberately different:
   - SCRIPT_RULES run over executable files (real code): network, exec, credential, obfuscation.
   - PROSE_RULES run over every markdown file (SKILL.md, reference.md, templates, examples) and only match *instructions to misbehave* — not security
     vocabulary, so a skill that legitimately discusses injection (threat-model) isn't flagged. */

const SCRIPT_EXT = new Set([".py", ".js", ".mjs", ".cjs", ".sh", ".bash", ".zsh", ".rb", ".pl", ".ps1"]);

const SCRIPT_RULES = [
  { id: "exec-remote", sev: "🟥", owasp: ["AST01", "AST02"], why: "downloads and executes remote content — the classic supply-chain payload",
    re: /(curl|wget)[^\n|]*\|\s*(sudo\s+)?(ba|z|)sh|eval\s*\(\s*(requests|urllib|fetch)|base64\s+(-d|--decode)[^\n|]*\|\s*(ba|z|)sh/i },
  { id: "shell-exec", sev: "🟧", owasp: ["AST03", "LLM06"], why: "executes shell commands",
    re: /\b(os\.system|subprocess\.(run|call|Popen|check_output)|child_process|execSync|spawnSync|shell_exec|`[^`\n]*\$\()/ },
  { id: "network", sev: "🟧", owasp: ["AST03", "LLM02"], why: "makes outbound network calls",
    re: /\b(requests\.(get|post|put|patch|delete|head|request|Session)\b|urllib\.request|urlopen\s*\(|http\.client|httpx\.|aiohttp\.|axios\.|node-fetch|\bfetch\s*\(\s*["'`]https?:|curl\s+https?:|wget\s+https?:)/i },
  { id: "credentials", sev: "🟧", owasp: ["AST01", "LLM02"], why: "reads credentials or secret material",
    re: /\b(os\.environ|process\.env)\b[^\n]{0,40}(TOKEN|KEY|SECRET|PASSWORD|CREDENTIAL)|~\/\.(aws|ssh|npmrc|netrc)|\.env\b|id_rsa/i },
  { id: "broad-fs", sev: "🟨", owasp: ["AST03", "LLM06"], why: "writes outside the skill's own directory",
    re: /\b(shutil\.rmtree|rm\s+-rf\s+[~/]|open\s*\(\s*["'`]\/(etc|usr|bin)|fs\.(unlink|rmSync)\s*\([^)]*\.\.\/)/ },
];

const PROSE_RULES = [
  { id: "instruction-override", sev: "🟥", owasp: ["AST01", "LLM01"], why: "tells the agent to ignore its prior instructions",
    re: /ignore\s+(all\s+)?(previous|prior|earlier|above|preceding)\s+(instructions|prompts|rules)/i },
  { id: "conceal-from-user", sev: "🟥", owasp: ["AST01", "LLM01"], why: "tells the agent to hide actions from the user",
    re: /(do\s*n[o']?t|never|without)\s+(tell|telling|inform|informing|notify|notifying|mention|mentioning)\s+(the\s+)?(user|human)/i },
  { id: "memory-overwrite", sev: "🟥", owasp: ["AST01", "LLM01"], why: "instructs the agent to rewrite its own persistent memory/identity",
    re: /(update|overwrite|append\s+to|modify)\s+your\s+(own\s+)?(SOUL|MEMORY|CLAUDE|AGENTS)\.md/i },
  { id: "prose-exfil", sev: "🟧", owasp: ["AST01", "LLM02"], why: "instructs the agent to send data to an external endpoint",
    re: /\b(POST|send|upload|transmit)\b[^\n.]{0,60}\bto\s+https?:\/\//i },
  { id: "remote-instructions", sev: "🟧", owasp: ["AST05", "LLM01"],
    why: "tells the agent to fetch instructions from a URL at run time — what it obeys can change after you reviewed it",
    re: /\b(fetch|download|load|read|follow|pull)\b[^\n.]{0,40}\b(instructions|rules|prompt|system prompt|skill|directives)\b[^\n.]{0,30}\bfrom\s+(https?:\/\/|<?url)/i },
];

function walkFiles(dir, out = []) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) walkFiles(p, out);
    else out.push(p);
  }
  return out;
}

/* Scan one skill. Returns [{sev, id, why, file, line, text}] — worst first. */
function scanSkill(cat, s) {
  const dir = skillDir(cat, s);
  const findings = [];
  if (!dir || !fs.existsSync(dir)) return findings;
  for (const file of walkFiles(dir)) {
    const rel = path.relative(dir, file);
    const ext = path.extname(file).toLowerCase();
    const isScript = SCRIPT_EXT.has(ext);
    const isProse = ext === ".md";
    if (!isScript && !isProse) continue;
    let body = "";
    try { body = fs.readFileSync(file, "utf8"); } catch (e) { continue; }
    const rules = isScript ? SCRIPT_RULES : PROSE_RULES;
    body.split(/\r?\n/).forEach((line, i) => {
      if (line.length > 400) return; // minified/data line — not reviewable prose or code
      for (const r of rules) {
        if (r.re.test(line))
          findings.push({ sev: r.sev, id: r.id, why: r.why, owasp: r.owasp, file: rel, line: i + 1, text: line.trim().slice(0, 120) });
      }
    });
  }
  findings.push(...permissionGaps(cat, s, findings));
  const order = { "🟥": 0, "🟧": 1, "🟨": 2, "⚪": 3 };
  return findings.sort((a, b) => order[a.sev] - order[b.sev]);
}

/* RFC-0039: compare what a skill's scripts do (the scan's script findings) with what its
   manifest says they do. A capability the code shows and the manifest doesn't declare is the
   finding that matters most: it is either an honest omission or something hiding. */
function permissionsOf(cat, s) {
  if (cat.shape === "apm") return null;
  try { return manifestOf(cat, s).permissions || null; } catch (e) { return null; }
}
function permissionGaps(cat, s, findings) {
  const dir = skillDir(cat, s);
  if (!dir || !fs.existsSync(path.join(dir, "scripts"))) return [];
  const perm = permissionsOf(cat, s);
  if (!perm)
    return [{ sev: "🟨", id: "no-permissions", owasp: ["AST03", "AST10"], file: "manifest.json", line: 0,
              why: "ships scripts but declares no permissions (network, commands, files) — nothing to check them against",
              text: "add a `permissions` block to manifest.json (RFC-0039)" }];
  const code = findings.filter((f) => SCRIPT_EXT.has(path.extname(f.file).toLowerCase()));
  const gaps = [];
  const gap = (id, f, why) => gaps.push({ sev: "🟥", id, owasp: ["AST03", "AST01"], why, file: f.file, line: f.line, text: f.text });
  for (const f of code) {
    if ((f.id === "network" || f.id === "exec-remote") && !(perm.network || []).length)
      gap("undeclared-network", f, "makes network calls, but the manifest declares no network hosts");
    if ((f.id === "shell-exec" || f.id === "exec-remote") && !(perm.commands || []).length)
      gap("undeclared-commands", f, "runs commands, but the manifest declares none");
    if (f.id === "broad-fs" && perm.files !== "anywhere")
      gap("undeclared-files", f, `writes outside its own paths, but the manifest declares files: "${perm.files}"`);
  }
  return gaps;
}
function permissionSummary(perm) {
  if (!perm) return "no permissions declared";
  const net = (perm.network || []).length ? `contacts ${perm.network.join(", ")}` : "no network";
  const cmds = (perm.commands || []).length ? `runs ${perm.commands.map((c) => c === "*" ? "commands you configure" : c).join(", ")}` : "runs no commands";
  const files = { none: "writes nothing", "named-paths": "writes only paths you name", project: "writes inside the project", anywhere: "writes anywhere" }[perm.files] || `files: ${perm.files}`;
  return `${net} · ${cmds} · ${files}`;
}

function printScan(cat, names, { compact = false } = {}) {
  let total = 0, worst = null;
  for (const s of names) {
    const f = scanSkill(cat, s);
    if (!f.length) continue;
    total += f.length;
    if (!worst || f[0].sev === "🟥") worst = worst === "🟥" ? worst : f[0].sev;
    console.log(`\n${s}`);
    for (const x of (compact ? f.slice(0, 3) : f))
      console.log(`  ${x.sev} ${x.id} — ${x.why}  [${x.owasp.join(", ")}]\n     ${x.file}:${x.line}  ${x.text}`);
    if (compact && f.length > 3) console.log(`     … ${f.length - 3} more (skilldrop scan ${s} --from ${cat.source})`);
  }
  return { total, worst };
}

function scan(args) {
  const cat = resolveCatalog(args.flags.from);
  const names = args._.length ? args._.slice() : skillsIn(cat);
  for (const s of names) if (!skillExists(cat, s)) die(`unknown skill '${s}' in catalog '${cat.source}'`);

  if (args.flags.json) {
    const out = names.map((s) => ({ skill: s, findings: scanSkill(cat, s) })).filter((r) => r.findings.length);
    return emitJSON({
      catalog: cat.source, scanned: names.length,
      flagged: out.length, findingCount: out.reduce((n, r) => n + r.findings.length, 0), skills: out,
    });
  }
  console.log(`Scanning ${names.length} skill(s) in catalog '${cat.source}' for supply-chain patterns…`);
  const { total } = printScan(cat, names);
  if (!total) {
    console.log("\nNo flagged patterns found.");
  } else {
    console.log(`\n${total} flagged pattern(s). These are HEURISTICS, not verdicts — a match can be` +
                ` entirely legitimate (a skill that is *about* security, or a script that genuinely needs the network).`);
    console.log("Read the cited lines before installing. Nothing here is executed by skilldrop; installs copy files only.");
    console.log("Tags are OWASP Agentic Skills Top 10 (AST) and LLM Top 10 2025 (LLM) IDs — guides/reference/owasp-mapping.md.");
  }
}

/* ---------- install targets & ledger ---------- */

/* Skill directories per tool: [project path, user path]. A null user path means the tool only
   reads skills from the repo. Paths are the ones each tool's own docs name, recorded with sources
   in docs/designs/ide-primitive-coverage.md. .agents/skills is shared: Codex, Antigravity and
   Copilot CLI all read it, so one project install reaches all three. */
const SKILL_DIRS = {
  claude: [[".claude", "skills"], [".claude", "skills"]],
  cursor: [[".cursor", "skills"], null],
  kiro: [[".kiro", "skills"], null],
  codex: [[".agents", "skills"], [".codex", "skills"]],
  antigravity: [[".agents", "skills"], [".gemini", "antigravity-cli", "skills"]],
  copilot: [[".github", "skills"], [".copilot", "skills"]],
};

function target(flags) {
  if (flags.dest) return { dest: path.resolve(flags.dest), ide: "generic" };
  const ide = flags.ide || "claude";
  const dirs = SKILL_DIRS[ide];
  if (!dirs) die(`unknown --ide '${ide}' (${Object.keys(SKILL_DIRS).join(" | ")}; use --dest for anything else)`);
  const [proj, user] = dirs;
  // --local is a project install the repo never sees (see localExclude), so it implies --project.
  if (flags.project || flags.local || !user) return { dest: path.resolve(...proj), ide };
  return { dest: path.join(os.homedir(), ...user), ide };
}

/* Claude Code tool name -> Kiro built-in tool name. Confirmed against
   kiro.dev/docs/cli/reference/built-in-tools/ — not inferred. Agent configs use these
   simplified names; Kiro's *hook* matchers use internal names (fs_read, execute_bash)
   instead, and mixing the two silently grants nothing. */
const KIRO_TOOLS = {
  Read: "read", Grep: "grep", Glob: "glob", Bash: "shell",
  Write: "write", Edit: "write", WebSearch: "web_search", WebFetch: "web_fetch",
};

function kiroAgentJSON(meta, body) {
  const declared = meta.tools ? meta.tools.split(",").map((s) => s.trim()).filter(Boolean) : [];
  const tools = [], unmapped = [];
  for (const d of declared) (KIRO_TOOLS[d] ? tools : unmapped).push(KIRO_TOOLS[d] || d);
  // The prompt is inlined rather than a file:// reference: the docs' example is
  // relative, but whether it resolves against the workspace root or the JSON file is
  // not stated, and a wrong path fails silently. One self-contained file cannot.
  const agent = { name: meta.name, description: meta.description, prompt: body, tools };
  // allowedTools is deliberately omitted — it is auto-approval, so leaving it out means
  // the user is prompted per tool call. Also sidesteps kirodotdev/Kiro#6714, where
  // allowedTools does not load as configured.
  return { json: JSON.stringify(agent, null, 2) + "\n", unmapped: [...new Set(unmapped)] };
}

/* Antigravity agent markdown (RFC-0013). Only mappings confirmed in Antigravity's own
   subagents doc are listed. There is no glob-style tool in its file tooling
   (view_file / list_dir / grep_search / write_to_file), so Glob is dropped and named
   rather than bent into list_dir — a different operation. */
const ANTIGRAVITY_TOOLS = { Read: "view_file", Grep: "grep_search", Bash: "run_command" };
const ANTIGRAVITY_MODELS = new Set(["inherit", "flash", "pro"]);

function antigravityAgentMD(meta, body) {
  const declared = meta.tools ? meta.tools.split(",").map((s) => s.trim()).filter(Boolean) : [];
  const tools = [], unmapped = [];
  for (const d of declared) (ANTIGRAVITY_TOOLS[d] ? tools : unmapped).push(ANTIGRAVITY_TOOLS[d] || d);
  // YAML double-quoted scalars are a superset of JSON strings, so JSON.stringify is a
  // correct quoter here — descriptions contain em-dashes and embedded quotes.
  const lines = [`name: ${JSON.stringify(meta.name)}`, `description: ${JSON.stringify(meta.description)}`];
  if (tools.length) lines.push(`tools: [${tools.join(", ")}]`);
  lines.push("subagent: true"); // required, or invoke_subagent cannot reach it
  if (ANTIGRAVITY_MODELS.has(meta.model)) lines.push(`model: ${meta.model}`);
  return { md: `---\n${lines.join("\n")}\n---\n\n${body}\n`, unmapped: [...new Set(unmapped)] };
}

/* Codex agent TOML. Schema confirmed at learn.chatgpt.com/docs/agent-configuration/subagents:
   name, description and developer_instructions are required; unknown fields are rejected.
   sandbox_mode is deliberately NOT emitted — Codex has no `tools` field, permissions come
   from sandbox_mode, and its permitted values are unconfirmed. Omitting it inherits the
   parent session, which is the only behaviour that can neither break the agent nor
   silently widen what it may do. */
function codexAgentTOML(meta, body) {
  const esc = (s) => s.replace(/\\/g, "\\\\").replace(/"/g, '\\"');
  const safe = body.includes('"""') ? body.replace(/"""/g, '\\"\\"\\"') : body;
  return `name = "${esc(meta.name)}"\n` +
         `description = "${esc(meta.description)}"\n` +
         `developer_instructions = """\n${safe}\n"""\n`;
}

/* Only plain-copy targets ship in RFC-0012. Everything else needs a projection the
   install-target model (RFC-0010) has not settled — so say so instead of guessing a path. */
const AGENT_MANUAL = {
  cursor: "a custom mode — Cursor has no agent file format",
};
function agentTarget(flags) {
  if (flags.dest) return { dest: path.resolve(flags.dest), ide: "generic" };
  const ide = flags.ide || "claude";
  if (ide === "claude")
    return flags.project
      ? { dest: path.resolve(".claude", "agents"), ide }
      : { dest: path.join(os.homedir(), ".claude", "agents"), ide };
  // Kiro and Copilot agent dirs are repo-relative by convention, so --project is implied.
  if (ide === "kiro") return { dest: path.resolve(".kiro", "agents"), ide };
  if (ide === "copilot") return { dest: path.resolve(".github", "agents"), ide };
  if (ide === "codex")
    return flags.project
      ? { dest: path.resolve(".codex", "agents"), ide }
      : { dest: path.join(os.homedir(), ".codex", "agents"), ide };
  if (ide === "antigravity")
    return flags.project
      ? { dest: path.resolve(".agents", "agents"), ide }
      : { dest: path.join(os.homedir(), ".gemini", "config", "agents"), ide };
  const hint = AGENT_MANUAL[ide];
  die(`--agent has no target for '${ide}'${hint ? ` — it needs ${hint}` : ""}.\n` +
      `       Copy it by hand (see agents/README.md), or use --dest <dir>. Tracked in RFC-0012.`);
}

/* Write one agent into a target, projecting only where the target's format demands it.
   Returns the filename written plus any warning worth printing. */
function writeAgent(cat, a, dest, ide) {
  const src = agentPath(cat, a);
  if (ide === "kiro") {
    const raw = fs.readFileSync(src, "utf8");
    const body = raw.split("---").slice(2).join("---").trim();
    const { json, unmapped } = kiroAgentJSON(agentMeta(cat, a), body);
    fs.writeFileSync(path.join(dest, `${a}.json`), json);
    return { file: `${a}.json`, warn: unmapped.length
      ? `  ${a}: no Kiro equivalent for ${unmapped.join(", ")} — dropped from tools, add by hand if needed`
      : null };
  }
  if (ide === "antigravity") {
    const raw = fs.readFileSync(src, "utf8");
    const body = raw.split("---").slice(2).join("---").trim();
    const { md, unmapped } = antigravityAgentMD(agentMeta(cat, a), body);
    fs.writeFileSync(path.join(dest, `${a}.md`), md);
    return { file: `${a}.md`, warn: unmapped.length
      ? `  ${a}: no Antigravity equivalent for ${unmapped.join(", ")} — dropped from tools, add by hand if needed`
      : null };
  }
  if (ide === "codex") {
    const raw = fs.readFileSync(src, "utf8");
    const body = raw.split("---").slice(2).join("---").trim();
    fs.writeFileSync(path.join(dest, `${a}.toml`), codexAgentTOML(agentMeta(cat, a), body));
    return { file: `${a}.toml`, warn: null };
  }
  const name = ide === "copilot" ? `${a}.agent.md` : `${a}.md`;
  fs.copyFileSync(src, path.join(dest, name));
  return { file: name, warn: null };
}

function ledger(dest) {
  const p = path.join(dest, LEDGER);
  return { path: p, data: fs.existsSync(p) ? readJSON(p) : {} };
}
// An empty ledger is removed rather than left behind, so uninstalling the last skill leaves no trace.
function saveLedger(l) {
  if (!Object.keys(l.data).length) return fs.rmSync(l.path, { force: true });
  fs.writeFileSync(l.path, JSON.stringify(l.data, null, 2) + "\n");
}
/* Ledger values: {version, source}; legacy plain strings mean a bundled install. */
function lver(v) { return typeof v === "string" ? v : v.version; }
function lsrc(v) { return typeof v === "string" ? BUNDLED : v.source || BUNDLED; }

/* Ask before a destructive step. Only a person at a terminal is asked: scripts, CI and pipes
   (stdin not a TTY) proceed as they always did, and --yes skips the question. */
function confirm(question, flags) {
  if (flags.yes || flags["dry-run"] || !process.stdin.isTTY) return true;
  process.stdout.write(`${question} [y/N] `);
  const buf = Buffer.alloc(256);
  let n = 0;
  try { n = fs.readSync(0, buf, 0, buf.length, null); } catch (e) { return false; }
  return /^y(es)?$/i.test(buf.toString("utf8", 0, n).trim());
}

/* Files in an installed skill that differ from the baseline the ledger recorded at copy time:
   the user's edits. Empty when there is no baseline (installed before RFC-0032). */
function editedFiles(dest, s, entry) {
  if (!entry || typeof entry !== "object" || !entry.files) return [];
  const out = [];
  for (const [rel, h] of Object.entries(entry.files)) {
    let mine = null;
    try { mine = sha256(fs.readFileSync(path.join(dest, s, ...rel.split("/")))); } catch (e) { /* deleted */ }
    if (mine !== null && mine !== h) out.push(rel);
  }
  return out;
}

/* --local: try skills in a repo you don't own. The install is a normal project install, and
   every path it writes is listed in the repo's own exclude file (.git/info/exclude, which git
   reads like .gitignore but never commits), so `git status` stays clean and nothing can be
   committed by accident. The entries live in one marker-fenced block this tool owns. */
const EXCLUDE_OPEN = "# >>> skilldrop --local >>>", EXCLUDE_CLOSE = "# <<< skilldrop --local <<<";
function excludePath(root) {
  try {
    const out = execFileSync("git", ["rev-parse", "--git-path", "info/exclude"],
      { cwd: root, encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] }).trim();
    if (out) return path.resolve(root, out);
  } catch (e) { /* no git binary */ }
  return path.join(root, ".git", "info", "exclude");
}
function readExclude(root) {
  const p = excludePath(root);
  const body = readIfPresent(p);
  const a = body.indexOf(EXCLUDE_OPEN), b = body.indexOf(EXCLUDE_CLOSE);
  const entries = a >= 0 && b > a
    ? body.slice(a + EXCLUDE_OPEN.length, b).split("\n").map((x) => x.trim()).filter(Boolean) : [];
  const rest = a >= 0 && b > a ? body.slice(0, a) + body.slice(b + EXCLUDE_CLOSE.length) : body;
  return { p, entries, rest: rest.replace(/\n{3,}/g, "\n\n") };
}
function writeExclude(root, entries) {
  const { p, rest } = readExclude(root);
  const sorted = [...new Set(entries)].sort();
  let body = rest.replace(/\s+$/, "");
  if (sorted.length) body += `${body ? "\n\n" : ""}${EXCLUDE_OPEN}\n${sorted.join("\n")}\n${EXCLUDE_CLOSE}`;
  fs.mkdirSync(path.dirname(p), { recursive: true });
  fs.writeFileSync(p, body ? body + "\n" : "");
  return p;
}
// Exclude patterns are repo-root-relative and anchored with a leading slash.
function excludeEntry(root, abs, dir) { return "/" + path.relative(root, abs).split(path.sep).join("/") + (dir ? "/" : ""); }
function localPaths(root, dest, ide, s) {
  const out = [excludeEntry(root, path.join(dest, s), true)];
  const w = wiringPath(ide, dest, s);
  if (w && ide === "cursor") out.push(excludeEntry(root, w, false));
  return out;
}
function addLocal(dest, ide, names) {
  const root = gitRoot(process.cwd());
  const { entries } = readExclude(root);
  const next = entries.concat(excludeEntry(root, path.join(dest, LEDGER), false));
  for (const s of names) next.push(...localPaths(root, dest, ide, s));
  return writeExclude(root, next);
}
/* Called on every uninstall, --local or not: dropping an entry that isn't there is a no-op, and
   the ledger's own entry goes once no skill in that folder is excluded any more. */
function removeLocal(dest, ide, names) {
  const root = gitRoot(process.cwd());
  if (!root) return null;
  const { entries } = readExclude(root);
  if (!entries.length) return null;
  const drop = new Set(names.flatMap((s) => localPaths(root, dest, ide, s)));
  let next = entries.filter((e) => !drop.has(e));
  const destPrefix = excludeEntry(root, dest, true);
  const ledgerEntry = excludeEntry(root, path.join(dest, LEDGER), false);
  if (!next.some((e) => e !== ledgerEntry && e.startsWith(destPrefix))) next = next.filter((e) => e !== ledgerEntry);
  if (next.length === entries.length) return null;
  return writeExclude(root, next);
}

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

/* Where git actually reads the pre-commit hook. In a worktree or a submodule .git is a file
   ("gitdir: ..."), not a folder, and core.hooksPath can move hooks anywhere — so ask git, and
   only fall back to .git/hooks when git isn't on the PATH. */
function preCommitPath(root) {
  try {
    const out = execFileSync("git", ["rev-parse", "--git-path", "hooks/pre-commit"],
      { cwd: root, encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] }).trim();
    if (out) return path.resolve(root, out);
  } catch (e) { /* no git binary, or not a repo after all */ }
  return path.join(root, ".git", "hooks", "pre-commit");
}

// Append an idempotent, marker-fenced reminder to the repo's pre-commit hook. IDE-agnostic.
function writeGitPreCommitHook(root, skill, hook) {
  const p = preCommitPath(root);
  const marker = `skilldrop-hook:${skill}:pre-commit-review`;
  let body = readIfPresent(p);  // read-and-handle, not check-then-read
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
  const raw = readIfPresent(settingsPath, null);
  if (raw !== null) {
    try { data = JSON.parse(raw); }
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
/* Claude Code reads settings.local.json beside settings.json and never expects it committed, so a
   --local install puts its session-start hook there instead of in the repo's shared settings. */
function claudeSettings(dest, local) { return path.join(path.dirname(dest), local ? "settings.local.json" : "settings.json"); }

function emitHooks(cat, skill, dest, ide, local) {
  let hooks = [];
  try { hooks = manifestOf(cat, skill).hooks || []; } catch (e) { return []; }
  const lines = [];
  for (const h of hooks) {
    if (h.event === "pre-commit-review") {
      const root = gitRoot(process.cwd());
      if (root) lines.push(`  ${skill}: pre-commit reminder -> ${preCommitPath(root)}`);
      else lines.push(`  ${skill}: pre-commit-review skipped — no git repo at ${process.cwd()}`);
      if (root) writeGitPreCommitHook(root, skill, h);
    } else if (h.event === "session-start") {
      if (ide === "claude") {
        const sp = claudeSettings(dest, local);
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
    const p = preCommitPath(root);
    const body = readIfPresent(p, null);
    if (body !== null) {
      const q = reEscape(skill);
      const re = new RegExp(`\\n?# >>> skilldrop-hook:${q}:[^\\n]* >>>[\\s\\S]*?# <<< skilldrop-hook:${q}:[^\\n]* <<<\\n?`, "g");
      const next = body.replace(re, "\n");
      if (next !== body) fs.writeFileSync(p, next);
    }
  }
  if (ide === "claude") for (const sp of [claudeSettings(dest, false), claudeSettings(dest, true)]) {
    const raw = readIfPresent(sp, null);
    if (raw !== null) {
      try {
        const data = JSON.parse(raw);
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

/* Packs that were renamed, so an old command or script keeps working. claude-api became
   api-builder in 0.13.9: Claude Code reserves plugin names that start with "claude-". */
const PACK_ALIASES = { "claude-api": "api-builder" };
function packAlias(flags, ps) {
  const n = flags.pack;
  if (n && ps && !ps[n] && PACK_ALIASES[n] && ps[PACK_ALIASES[n]]) {
    console.error(`note: pack '${n}' is now '${PACK_ALIASES[n]}' — use --pack ${PACK_ALIASES[n]}`);
    flags.pack = PACK_ALIASES[n];
  }
}

function expandNames(args, cat) {
  if (args.flags.all) return skillsIn(cat);
  if (args.flags.pack) {
    const ps = packsOf(cat);
    if (!ps) die(`catalog '${cat.source}' defines no packs — install skills by name`);
    packAlias(args.flags, ps);
    const p = ps[args.flags.pack];
    if (!p) die(`unknown pack '${args.flags.pack}' in catalog '${cat.source}'`);
    return packMembers(ps, args.flags.pack, "skills");
  }
  if (!args._.length) die("nothing to install — pass skill names, --pack <name>, or --all");
  for (const s of args._) if (!skillExists(cat, s)) die(`unknown skill '${s}' in catalog '${cat.source}'`);
  return args._.slice();
}

function copyOne(cat, s, dest, ide, l, notes) {
  const m = manifestOf(cat, s);
  fs.cpSync(skillDir(cat, s), path.join(dest, s), { recursive: true });
  const note = writeWiring(ide, dest, s, m.description);
  if (note && notes) notes.push(note);
  l.data[s] = { version: m.version, source: cat.source, files: fileHashes(skillDir(cat, s)) };
  if (cat.commit) l.data[s].commit = cat.commit;
  return m;
}

/* RFC-0032: per-file SHA-256 of a skill as the catalog shipped it, recorded in the ledger at
   copy time. It is the baseline `update` compares against, so a file the user edited is never
   overwritten. Paths are forward-slash relative; *.upstream files are this tool's output. */
function sha256(buf) { return crypto.createHash("sha256").update(buf).digest("hex"); }
function fileHashes(dir) {
  const out = {};
  (function walk(d, rel) {
    for (const e of fs.readdirSync(d, { withFileTypes: true })) {
      const r = rel ? `${rel}/${e.name}` : e.name;
      if (e.isDirectory()) walk(path.join(d, e.name), r);
      else if (e.isFile() && !e.name.endsWith(".upstream")) out[r] = sha256(fs.readFileSync(path.join(d, e.name)));
    }
  })(dir, "");
  return out;
}

/* Update one skill file by file against the ledger baseline (RFC-0032):
     upstream unchanged            -> leave the local file alone, edited or not
     local untouched, or new file  -> take the new version
     local edited, upstream moved  -> keep the local file, write the new one as <file>.upstream
   A file the catalog dropped is removed only if the user never touched it. The new baseline is
   what the catalog ships now, so a kept edit stays "edited" until the user merges it. */
function mergeOne(cat, s, dest, ide, l, notes, dry = false) {
  const m = manifestOf(cat, s);
  const src = skillDir(cat, s), dst = path.join(dest, s);
  const base = l.data[s].files, next = fileHashes(src);
  const kept = [], orphaned = [];
  const at = (root, rel) => path.join(root, ...rel.split("/"));
  const localHash = (rel) => { try { return sha256(fs.readFileSync(at(dst, rel))); } catch (e) { return null; } };
  for (const [rel, h] of Object.entries(next)) {
    const mine = localHash(rel), to = at(dst, rel);
    if (mine === h) { if (!dry) fs.rmSync(to + ".upstream", { force: true }); continue; }
    if (h === base[rel]) continue;
    if (mine === null ? !(rel in base) : mine === base[rel]) {
      if (dry) continue;
      fs.mkdirSync(path.dirname(to), { recursive: true });
      fs.copyFileSync(at(src, rel), to);
      fs.rmSync(to + ".upstream", { force: true });
    } else {
      kept.push(rel);
      if (dry) continue;
      fs.mkdirSync(path.dirname(to), { recursive: true });
      fs.copyFileSync(at(src, rel), to + ".upstream");
    }
  }
  for (const rel of Object.keys(base)) {
    if (rel in next) continue;
    const mine = localHash(rel);
    if (mine === base[rel]) { if (!dry) fs.rmSync(at(dst, rel), { force: true }); }
    else if (mine !== null) orphaned.push(rel);
  }
  if (dry) return { m, kept, orphaned };
  const note = writeWiring(ide, dest, s, m.description);
  if (note && notes) notes.push(note);
  l.data[s] = { version: m.version, source: cat.source, files: next };
  if (cat.commit) l.data[s].commit = cat.commit;
  return { m, kept, orphaned };
}

/* Install a whole review panel — the reviewer subagents + the orchestrator skill — in one
   command (RFC-0020). Needs a target with BOTH a subagent and a skill format, so it accepts
   the default (Claude Code), --project, --ide kiro, or --dest; other IDEs install the halves
   separately. Delegates to installAgents + install so every existing safety/craft gate applies. */
const PANEL_IDES = ["kiro", "codex", "antigravity", "copilot"];
function installPanel(args) {
  const name = args.flags.panel;
  const p = PANELS[name];
  if (!p) die(`unknown panel '${name}' — available: ${Object.keys(PANELS).join(", ")}`);
  const ide = args.flags.ide;
  if (ide && !PANEL_IDES.includes(ide) && !args.flags.dest)
    die(`--panel installs subagents + the orchestrator skill together, so it needs a target with both formats:\n` +
        `       (default | --project) Claude Code, --ide ${PANEL_IDES.join(" | ")}, or --dest <dir>.\n` +
        `       For ${ide}: install the agents (skilldrop install --agent ${p.agents.join(" ")} --ide ${ide}) ` +
        `and the skill (skilldrop install ${p.skill} --ide ${ide}) separately.`);
  const flags = Object.assign({}, args.flags);
  delete flags.panel;
  console.log(`Installing the '${name}' panel — ${p.agents.length} reviewer subagents + the ${p.skill} orchestrator skill.\n`);
  installAgents({ _: p.agents.slice(), flags: Object.assign({}, flags, { agent: true }) });
  console.log("");
  install({ _: [p.skill], flags });
  console.log(`\nPanel installed. Fire it with the ${p.skill} skill — e.g. "run a pre-merge review on this change".`);
  console.log(`It dispatches the three subagents in parallel where your tool has native subagents (Claude Code today;`);
  console.log(`Codex / Antigravity multi-agent runners), and sweeps the lenses inline otherwise. Per-tool: agents/README.md.`);
}

function listProfiles(args) {
  const cat = resolveCatalog(args.flags.from);
  const ps = profilesOf(cat);
  if (args.flags.json)
    return emitJSON({
      catalog: cat.source,
      count: ps ? Object.keys(ps).length : 0,
      profiles: Object.entries(ps || {}).map(([name, p]) => ({
        name, description: p.description || null,
        packs: p.packs || [], agents: p.agents || [], loops: p.loops || [],
      })),
    });
  if (!ps) return console.log(`catalog '${cat.source}' defines no profiles.`);
  const w = Math.max(...Object.keys(ps).map((n) => n.length));
  for (const [n, p] of Object.entries(ps))
    console.log(`${n.padEnd(w)}  ${p.description}`);
  console.log("\nInstall one: skilldrop install --profile <name>");
}

function installProfile(args) {
  const name = args.flags.profile;
  const cat = resolveCatalog(args.flags.from);
  const profiles = profilesOf(cat);
  if (!profiles) die(`catalog '${cat.source}' has no profiles.json`);
  const p = profiles[name];
  if (!p) die(`unknown profile '${name}' — available: ${Object.keys(profiles).join(", ")}`);

  console.log(`Installing profile '${name}': ${p.description}\n`);
  const flags = Object.assign({}, args.flags);
  delete flags.profile;

  for (const pack of (p.packs || [])) {
    console.log(`\n── pack: ${pack} ──`);
    install({ _: [], flags: Object.assign({}, flags, { pack }) });
  }
  for (const loop of (p.loops || [])) {
    if (loopsIn(cat).includes(loop)) {
      console.log(`\n── loop: ${loop} ──`);
      installLoops({ _: [loop], flags: Object.assign({}, flags, { loop: true }) });
    }
  }
  if ((p.agents || []).length) {
    console.log(`\n── agents: ${p.agents.join(", ")} ──`);
    installAgents({ _: p.agents.slice(), flags: Object.assign({}, flags, { agent: true }) });
  }
  console.log(`\nProfile '${name}' installed.`);
}

function install(args) {
  if (args.flags["dry-run"] && (args.flags.panel || args.flags.profile || args.flags.loop || args.flags.agent))
    die("--dry-run covers skill installs, update and uninstall. To preview a panel, profile, loop or agent,\n" +
        "       read what it contains first: skilldrop profiles | loops | agents --json");
  if (args.flags.local && !gitRoot(process.cwd()))
    die("--local hides the install from git, so it needs a git repo — run it from inside one");
  if (args.flags.local && (args.flags.panel || args.flags.profile || args.flags.agent))
    die("--local covers skills and loops. Agents have their own folders; install them with --dest into a path you exclude yourself");
  if (args.flags.panel) return installPanel(args);
  if (args.flags.profile) return installProfile(args);
  if (args.flags.loop) return installLoops(args);
  if (args.flags.agent) return installAgents(args);
  const cat = resolveCatalog(args.flags.from);
  let names = expandNames(args, cat);
  if (args.flags["with-related"]) {
    const seen = new Set(names);
    for (const s of names.slice()) {
      let related = [];
      try { related = manifestOf(cat, s).related || []; } catch (e) { /* gated below */ }
      for (const r of related) if (!seen.has(r) && skillExists(cat, r)) { seen.add(r); names.push(r); }
    }
  }
  gate(cat, names);
  const { dest, ide } = target(args.flags);
  if (args.flags["dry-run"]) return planInstall(cat, names, dest, ide, args.flags);
  fs.mkdirSync(dest, { recursive: true });
  const l = ledger(dest);
  const pipDeps = [], suggestions = new Set(), notes = [];
  for (const s of names) {
    const m = copyOne(cat, s, dest, ide, l, notes);
    if (fs.existsSync(path.join(skillDir(cat, s), "requirements.txt"))) pipDeps.push(s);
    for (const r of m.related || []) if (!names.includes(r) && !l.data[r]) suggestions.add(r);
    console.log(`installed ${s}@${m.version} -> ${dest}`);
  }
  saveLedger(l);
  console.log(`\n${names.length} skill(s) installed (${ide}).`);
  if (notes.length) console.log(`\nCleanup:\n${notes.join("\n")}`);
  const local = !!args.flags.local;
  if (local) {
    const ex = addLocal(dest, ide, names);
    console.log(`\n--local: listed in ${path.relative(process.cwd(), ex) || ex}, so git won't see these files.` +
                `\n  Nothing in the repo's tracked files changed. Remove with: skilldrop uninstall <skill> --local`);
  }

  const withHooks = names.filter((s) => { try { return (manifestOf(cat, s).hooks || []).length; } catch (e) { return false; } });
  if (withHooks.length && args.flags["with-hooks"]) {
    const lines = withHooks.flatMap((s) => emitHooks(cat, s, dest, ide, local));
    if (local && ide === "claude") {
      const root = gitRoot(process.cwd());
      writeExclude(root, readExclude(root).entries.concat(excludeEntry(root, claudeSettings(dest, true), false)));
    }
    console.log(`\nHooks wired (RFC-0006):\n${lines.join("\n")}`);
    if (cat.source !== BUNDLED)
      console.log(`  NOTE: these hooks run commands from third-party catalog '${cat.source}' — read them before trusting them.`);
    console.log(`  Undo any of these with: skilldrop uninstall <skill> ${ide === "claude" ? "" : "--ide " + ide}`.trimEnd());
  } else if (withHooks.length) {
    console.log(`\n${withHooks.join(", ")} declare hooks — re-run with --with-hooks to wire them (git pre-commit reminders / session-start context).`);
  }

  if (cat.source !== BUNDLED && cat.commit) {
    if (cat.pinned) console.log(`\nPinned: these skills came from commit ${cat.commit.slice(0, 12)}, as requested.`);
    else console.log(`\nNot pinned: '${cat.source}' can change after you review it. These skills came from commit ${cat.commit.slice(0, 12)};` +
                     `\n  to get exactly these files again, install with --from ${splitSource(cat.source)[0]}#${cat.commit}`);
  }
  if (cat.source !== BUNDLED) {
    console.log(`\nWARNING: third-party catalog '${cat.source}'. Skills are instructions your AI agent will follow — review each installed SKILL.md under ${dest} before first use. Install copied files only; nothing was executed.`);
    // Supply-chain scan (RFC-0022): surface risky patterns at the moment of trust. Reports only —
    // the files are already copied, and a match is a prompt to read, not a verdict.
    const scripted = names.filter((s) => fs.existsSync(path.join(skillDir(cat, s), "scripts")));
    if (scripted.length) {
      console.log(`\nWhat the scripts declare they do (RFC-0039):`);
      for (const s of scripted) console.log(`  ${s}: ${permissionSummary(permissionsOf(cat, s))}`);
    }
    const { total } = printScan(cat, names, { compact: true });
    console.log(total
      ? `\n${total} pattern(s) worth reading before you trust these skills. Full detail: skilldrop scan --from ${cat.source}`
      : "\nSupply-chain scan: no flagged patterns.");
  }
  if (ide === "generic")
    console.log("wiring: attach each skill's SKILL.md to your agent (Continue/Cline: @file, Aider: /add) — see the repo README's per-IDE steps.");
  for (const s of pipDeps)
    console.log(`deps: ${s} needs Python packages — run: cd ${path.join(dest, s)} && python3 -m pip install -r requirements.txt`);
  if (suggestions.size)
    console.log(`related (not installed): ${[...suggestions].sort().join(", ")} — add --with-related or install by name.`);
  const pk = args.flags.pack && (packsOf(cat) || {})[args.flags.pack];
  if (pk && pk["first-value"]) console.log("\n" + firstValueLines(pk).join("\n"));
}

/* install --dry-run: everything install would write, and nothing written. */
function planInstall(cat, names, dest, ide, flags) {
  const l = ledger(dest);
  console.log(`dry run — nothing will be written. Target: ${dest} (${ide})\n`);
  for (const s of names) {
    const m = manifestOf(cat, s);
    const have = l.data[s];
    const verb = !have ? "install" : lver(have) === m.version ? "reinstall" : `replace ${lver(have)} with`;
    const edits = editedFiles(dest, s, have);
    console.log(`would ${verb} ${s}@${m.version} -> ${path.join(dest, s)}`);
    if (edits.length) console.log(`  overwrites your edits in: ${edits.join(", ")} (update keeps them; install does not)`);
    const w = wiringPath(ide, dest, s);
    if (w && ide === "cursor") console.log(`  and write ${path.relative(process.cwd(), w)}`);
  }
  if (flags.local) {
    const root = gitRoot(process.cwd());
    console.log(`\n--local: would list ${names.length} folder(s) and the ledger in ${path.relative(process.cwd(), excludePath(root))}`);
  }
  if (flags["with-hooks"]) {
    const hooked = names.filter((s) => { try { return (manifestOf(cat, s).hooks || []).length; } catch (e) { return false; } });
    if (hooked.length) console.log(`\nwould wire hooks for: ${hooked.join(", ")}`);
  }
  console.log(`\n${names.length} skill(s). Rerun without --dry-run to install.`);
}

function installedRows(flags) {
  const { dest, ide } = target(flags);
  const l = ledger(dest);
  const rows = Object.keys(l.data).sort().map((s) => {
    const src = lsrc(l.data[s]);
    let current = null, cat = null, changed = [];
    const entry = l.data[s];
    try {
      cat = resolveCatalog(src === BUNDLED ? undefined : src);
      if (skillExists(cat, s)) {
        current = manifestOf(cat, s).version;
        // Same version, different files: the catalog changed the skill without bumping it.
        // The version check alone would never see that (OWASP AST07, update drift).
        if (current === lver(entry) && typeof entry === "object" && entry.files) {
          const now = fileHashes(skillDir(cat, s));
          changed = [...new Set([...Object.keys(now), ...Object.keys(entry.files)])]
            .filter((f) => now[f] !== entry.files[f]).sort();
        }
      }
    } catch (e) { /* unreachable source: current stays null */ }
    return { s, src, cat, installed: lver(entry), current, changed, pinned: isPinned(src) };
  });
  return { dest, ide, l, rows };
}

function update(args) {
  const { dest, ide, l, rows } = installedRows(args.flags);
  if (!rows.length) return console.log(`nothing installed at ${dest}`);
  const dry = !!args.flags["dry-run"];
  // A row is due when its version moved, or (with --changed) when its files moved under the
  // same version. Same-version changes are never taken silently: they are named and skipped.
  const isDue = (r) => r.current && (r.current !== r.installed || (args.flags.changed && r.changed.length));
  const due = rows.filter(isDue);
  if (args.flags.force && !dry) {
    const lost = due.flatMap((r) => editedFiles(dest, r.s, l.data[r.s]).map((f) => `${r.s}/${f}`));
    if (lost.length) {
      console.log(`--force overwrites ${lost.length} file(s) you edited:\n  ${lost.join("\n  ")}`);
      if (!confirm("Overwrite them?", args.flags)) return console.log("cancelled — nothing changed. Drop --force to keep your edits as <file>.upstream.");
    }
  }
  if (dry) return planUpdate(dest, ide, l, rows, args.flags);
  let n = 0, conflicts = 0;
  const silent = rows.filter((r) => r.current === r.installed && r.changed.length && !args.flags.changed);
  for (const r of rows) {
    if (!r.current) { console.log(`skip ${r.s}: source '${r.src}' unreachable or skill gone from it`); continue; }
    if (!isDue(r)) continue;
    const problems = checkSkill(r.cat, r.s);
    if (problems.length) { console.log(`skip ${r.s}: fails structural check in '${r.src}' (${problems[0]})`); continue; }
    // No baseline (installed before RFC-0032) or --force: overwrite as before, and record one.
    const entry = l.data[r.s];
    if (args.flags.force || typeof entry !== "object" || !entry.files) {
      copyOne(r.cat, r.s, dest, ide, l);
      console.log(`updated ${r.s} ${r.installed === r.current ? `${r.current} (same version, changed upstream)` : `${r.installed} -> ${r.current}`} (${r.src})`);
    } else {
      const { kept, orphaned } = mergeOne(r.cat, r.s, dest, ide, l);
      console.log(`updated ${r.s} ${r.installed === r.current ? `${r.current} (same version, changed upstream)` : `${r.installed} -> ${r.current}`} (${r.src})`);
      for (const f of kept) console.log(`  kept your edits in ${f} — new version at ${f}.upstream`);
      for (const f of orphaned) console.log(`  kept ${f} — dropped upstream, but you edited it`);
      conflicts += kept.length;
    }
    n++;
  }
  saveLedger(l);
  console.log(n ? `\n${n} skill(s) updated.` : (silent.length ? "no version changes." : "everything up to date."));
  if (silent.length)
    console.log(`\nNot taken: ${silent.map((r) => r.s).join(", ")} changed upstream without a version bump.` +
                `\n  Read the change (skilldrop diff <skill>), then take it with: skilldrop update --changed`);
  const pinned = rows.filter((r) => r.pinned);
  if (pinned.length)
    console.log(`\n${pinned.length} skill(s) come from a catalog pinned to a commit, so they stay as they are. To move them,` +
                `\n  reinstall with the new commit: skilldrop install <skill> --from <url>#<new-commit>`);
  // An update is a fresh act of trust in a third-party catalog (OWASP AST07): scan what changed.
  const thirdParty = {};
  for (const r of rows) if (isDue(r) && r.src !== BUNDLED) (thirdParty[r.src] = thirdParty[r.src] || { cat: r.cat, names: [] }).names.push(r.s);
  for (const { cat, names } of Object.values(thirdParty)) {
    const { total } = printScan(cat, names, { compact: true });
    console.log(total ? `\n${total} pattern(s) in the updated skills from '${cat.source}' worth reading. Full detail: skilldrop scan --from ${cat.source}`
                      : `\nSupply-chain scan of the updated skills from '${cat.source}': no flagged patterns.`);
  }
  if (conflicts)
    console.log(`${conflicts} file(s) kept your edits. Merge each <file>.upstream into its file, then delete it — or rerun with --force to take every new version.`);
}

/* update --dry-run: the same per-skill, per-file decisions update makes, reported, not applied. */
function planUpdate(dest, ide, l, rows, flags) {
  console.log(`dry run — nothing will be written. Target: ${dest} (${ide})\n`);
  let n = 0;
  for (const r of rows) {
    if (!r.current) { console.log(`would skip ${r.s}: source '${r.src}' unreachable or skill gone from it`); continue; }
    if (r.current === r.installed && !r.changed.length) continue;
    if (r.current === r.installed && !flags.changed) {
      console.log(`would not take ${r.s}: ${r.changed.length} file(s) changed upstream without a version bump (add --changed to take them)`);
      continue;
    }
    const problems = checkSkill(r.cat, r.s);
    if (problems.length) { console.log(`would skip ${r.s}: fails structural check (${problems[0]})`); continue; }
    n++;
    const entry = l.data[r.s];
    console.log(`would update ${r.s} ${r.installed} -> ${r.current} (${r.src})`);
    if (flags.force || typeof entry !== "object" || !entry.files) {
      const lost = editedFiles(dest, r.s, entry);
      if (lost.length) console.log(`  --force overwrites your edits in: ${lost.join(", ")}`);
      continue;
    }
    const { kept, orphaned } = mergeOne(r.cat, r.s, dest, ide, l, null, true);
    for (const f of kept) console.log(`  would keep your edits in ${f} and write the new version to ${f}.upstream`);
    for (const f of orphaned) console.log(`  would keep ${f} — dropped upstream, but you edited it`);
  }
  const held = rows.filter((r) => r.current && r.current === r.installed && r.changed.length && !flags.changed).length;
  console.log(n ? `\n${n} skill(s) would update. Rerun without --dry-run to apply.` : (held ? "no version changes." : "everything up to date."));
}

function outdated(args) {
  const { dest, rows } = installedRows(args.flags);
  const stale = rows.filter((r) => r.current && r.current !== r.installed);
  const drift = rows.filter((r) => r.changed && r.changed.length);
  if (args.flags.json)
    return emitJSON({
      dest,
      count: rows.length,
      outdatedCount: stale.length,
      changedWithoutVersionCount: drift.length,
      skills: rows.map((r) => ({
        name: r.s, installed: r.installed, current: r.current,
        source: r.src, outdated: !!(r.current && r.current !== r.installed),
        changedWithoutVersion: r.changed || [], pinned: r.pinned,
      })),
    });
  if (!rows.length) return console.log(`nothing installed at ${dest}`);
  for (const r of stale) console.log(`${r.s}: installed ${r.installed}, current ${r.current} (${r.src})`);
  for (const r of drift)
    console.log(`${r.s}: ${r.changed.length} file(s) changed in '${r.src}' without a version bump (${r.changed.slice(0, 3).join(", ")}${r.changed.length > 3 ? ", …" : ""})`);
  if (drift.length)
    console.log(`\n${drift.length} skill(s) changed upstream with the same version. Read the change first (skilldrop diff <skill>),` +
                `\nthen take it with: skilldrop update --changed`);
  console.log(stale.length ? `\n${stale.length} outdated — run: skilldrop update` : (drift.length ? "" : "everything up to date."));
}

function uninstall(args) {
  if (args.flags.agent) return uninstallAgents(args);
  if (args.flags.loop) return uninstallLoops(args);
  if (!args._.length) die("pass skill names to uninstall");
  const { dest, ide } = target(args.flags);
  const l = ledger(dest);
  const present = args._.filter((s) => l.data[s] || fs.existsSync(path.join(dest, s)));
  const missing = args._.filter((s) => !present.includes(s));
  for (const s of missing) console.log(`${s} is not installed at ${dest}`);
  if (!present.length) return;
  const edits = present.flatMap((s) => editedFiles(dest, s, l.data[s]).map((f) => `${s}/${f}`));
  if (args.flags["dry-run"]) {
    console.log(`dry run — nothing will be removed. Target: ${dest} (${ide})\n`);
    for (const s of present) {
      console.log(`would remove ${path.join(dest, s)}`);
      const w = wiringPath(ide, dest, s);
      if (w && fs.existsSync(w)) console.log(`  and ${path.relative(process.cwd(), w)}`);
    }
    if (edits.length) console.log(`\nincluding ${edits.length} file(s) you edited: ${edits.join(", ")}`);
    return;
  }
  const what = `Remove ${present.length} skill(s) from ${dest}: ${present.join(", ")}` +
               (edits.length ? `\n  (${edits.length} of the files have your edits: ${edits.join(", ")})` : "") + "?";
  if (!confirm(what, args.flags)) return console.log("cancelled — nothing removed.");
  for (const s of present) {
    fs.rmSync(path.join(dest, s), { recursive: true, force: true });
    const w = wiringPath(ide, dest, s);
    if (w) fs.rmSync(w, { force: true });
    removeHooksFor(s, dest, ide);
    delete l.data[s];
    console.log(`removed ${s} from ${dest}`);
  }
  saveLedger(l);
  const ex = removeLocal(dest, ide, present);
  if (ex) console.log(`dropped the --local entries from ${path.relative(process.cwd(), ex) || ex}`);
}

/* diff <skill>: what differs between the installed copy and the catalog's current one — your
   edits, an upstream change, or both. File-level always; line-level through git when it is on
   the PATH (git diff --no-index works outside any repo). */
function diff(args) {
  const s = args._[0] || die("pass an installed skill name: skilldrop diff <skill>");
  const { dest } = target(args.flags);
  const l = ledger(dest);
  const entry = l.data[s];
  if (!entry && !fs.existsSync(path.join(dest, s))) die(`'${s}' is not installed at ${dest}`);
  if (entry && entry.loop) die(`'${s}' is a loop — diff compares skills`);
  const src = args.flags.from || (entry ? lsrc(entry) : BUNDLED);
  const cat = resolveCatalog(src === BUNDLED ? undefined : src);
  if (!skillExists(cat, s)) die(`'${s}' is no longer in catalog '${cat.source}'`);
  const theirs = fileHashes(skillDir(cat, s)), mine = fileHashes(path.join(dest, s));
  const base = (entry && entry.files) || {};
  const changed = Object.keys(theirs).filter((f) => f in mine && mine[f] !== theirs[f]).sort();
  const onlyUp = Object.keys(theirs).filter((f) => !(f in mine)).sort();
  const onlyMine = Object.keys(mine).filter((f) => !(f in theirs)).sort();
  const why = (f) => !base[f] ? "" : mine[f] !== base[f] && theirs[f] !== base[f] ? "  (you edited it, and so did the catalog)"
    : mine[f] !== base[f] ? "  (your edit)" : "  (catalog changed it)";
  const iv = entry ? lver(entry) : "?", cv = manifestOf(cat, s).version;
  console.log(`${s}: installed ${iv} at ${path.join(dest, s)}  vs  catalog '${cat.source}' ${cv}`);
  if (!changed.length && !onlyUp.length && !onlyMine.length) return console.log("identical.");
  for (const f of changed) console.log(`  M ${f}${why(f)}`);
  for (const f of onlyUp) console.log(`  + ${f}  (in the catalog, not installed)`);
  for (const f of onlyMine) console.log(`  - ${f}  (installed only)`);
  if (args.flags.stat) return;
  let git = true;
  for (const f of changed) {
    const a = path.join(skillDir(cat, s), ...f.split("/")), b = path.join(dest, s, ...f.split("/"));
    try {
      execFileSync("git", ["--no-pager", "diff", "--no-index", "--color=auto", "--src-prefix=catalog/", "--dst-prefix=installed/", a, b],
        { stdio: ["ignore", "inherit", "inherit"] });
    } catch (e) {
      if (e.code === "ENOENT") { git = false; break; } // no git binary
      // exit status 1 is git diff's "files differ" — the expected case
    }
  }
  if (!git) console.log("\n(git not found — line-level diff needs git on the PATH; file list above)");
  if (changed.length) console.log(`\nTake the catalog's version: skilldrop update --force, or install ${s} again.`);
}

/* doctor: check an install target against its ledger and report what's out of step — skills
   recorded but gone, skills on disk nobody recorded, leftover .upstream files, wiring and hooks
   for skills no longer installed. Report-only: it changes nothing, and each finding says the fix. */
function doctor(args) {
  const { dest, ide } = target(args.flags);
  const findings = [];
  const add = (level, msg, fix) => findings.push({ level, msg, fix });
  const lp = path.join(dest, LEDGER);
  let data = {};
  const raw = readIfPresent(lp, null);
  if (raw === null) add("info", `no ledger at ${lp}`, "nothing installed here by skilldrop — or a different target; try --project or --ide");
  else try { data = JSON.parse(raw); } catch (e) { add("error", `${lp} is not valid JSON`, "fix or delete it; skilldrop can't track updates until then"); }
  const names = Object.keys(data);
  for (const n of names) {
    if (!fs.existsSync(path.join(dest, n))) add("error", `${n} is in the ledger but its folder is gone`, `skilldrop install ${n} (or uninstall ${n} to drop the record)`);
    else if (!data[n].loop && !data[n].file) {
      const e = editedFiles(dest, n, data[n]);
      if (e.length) add("info", `${n}: you edited ${e.join(", ")}`, `skilldrop diff ${n}`);
      if (typeof data[n] === "string" || !data[n].files) add("warn", `${n} has no file baseline (installed before 0.13)`, `skilldrop install ${n} once; update will keep your edits after that`);
    }
  }
  if (fs.existsSync(dest)) {
    for (const d of fs.readdirSync(dest, { withFileTypes: true })) {
      if (!d.isDirectory()) continue;
      const dir = path.join(dest, d.name);
      if (fs.existsSync(path.join(dir, "SKILL.md")) && !data[d.name])
        add("info", `${d.name} is on disk but not in the ledger`, "installed by hand or another tool — skilldrop won't update it");
      for (const f of walkFiles(dir)) if (f.endsWith(".upstream"))
        add("warn", `${path.relative(dest, f)} is waiting to be merged`, `merge it into ${path.relative(dest, f.slice(0, -9))}, then delete it`);
    }
  }
  if (ide === "cursor") {
    const rules = path.join(path.dirname(dest), "rules");
    for (const f of fs.existsSync(rules) ? fs.readdirSync(rules) : []) {
      const body = readIfPresent(path.join(rules, f));
      const m = body.match(/\.cursor\/skills\/([^/\s]+)\/SKILL\.md/);
      if (m && !fs.existsSync(path.join(dest, m[1]))) add("warn", `.cursor/rules/${f} points at ${m[1]}, which isn't installed`, `delete .cursor/rules/${f}`);
    }
  }
  if (ide === "kiro") for (const n of names) {
    const w = wiringPath("kiro", dest, n);
    if (readIfPresent(w).startsWith(KIRO_SHIM_PREFIX)) add("warn", `stale steering shim ${path.relative(process.cwd(), w)}`, `skilldrop install ${n} --ide kiro removes it`);
  }
  const root = gitRoot(process.cwd());
  if (root) {
    const hook = readIfPresent(preCommitPath(root));
    for (const m of hook.matchAll(/# >>> skilldrop-hook:([^:\n]+):/g))
      if (!fs.existsSync(path.join(dest, m[1])) && !data[m[1]]) add("warn", `pre-commit reminder for ${m[1]}, which isn't installed here`, `skilldrop uninstall ${m[1]} removes it (or it belongs to another target)`);
    for (const e of readExclude(root).entries)
      if (!fs.existsSync(path.join(root, e.replace(/^\//, "")))) add("info", `--local entry ${e} matches nothing`, "harmless; skilldrop uninstall --local tidies it");
  }
  if (ide === "claude") for (const local of [false, true]) {
    const sp = claudeSettings(dest, local);
    const body = readIfPresent(sp, null);
    if (body === null) continue;
    for (const m of body.matchAll(/skilldrop-hook:([^:"\s]+):session-start/g))
      if (!fs.existsSync(path.join(dest, m[1]))) add("warn", `${path.basename(sp)} has a session-start hook for ${m[1]}, which isn't installed`, `skilldrop uninstall ${m[1]} removes it`);
  }
  if (args.flags.json) return emitJSON({ dest, ide, installed: names.length, findings });
  console.log(`skilldrop doctor — ${dest} (${ide}), ${names.length} recorded\n`);
  const icon = { error: "✗", warn: "!", info: "·" };
  for (const f of findings) console.log(`${icon[f.level]} ${f.msg}\n    fix: ${f.fix}`);
  const bad = findings.filter((f) => f.level !== "info").length;
  console.log(findings.length ? `\n${bad} to fix, ${findings.length - bad} for information. Nothing was changed.` : "all good.");
}

/* new-skill <name> --pack <pack>: scaffold a skill in the catalog you're standing in, with every
   file validate.py checks for, so the first run fails only on the parts that need a human. */
function newSkill(args) {
  const name = args._[0] || die("usage: skilldrop new-skill <name> --pack <pack> [--tier light|standard|heavy]");
  if (!/^[a-z][a-z0-9]*(-[a-z0-9]+)*$/.test(name)) die(`'${name}' isn't kebab-case — use lowercase words joined by hyphens`);
  const pack = args.flags.pack || die("pass --pack <pack> — the one pack it belongs in (core only if every role needs it)");
  const tier = args.flags.tier || "standard";
  if (!["light", "standard", "heavy"].includes(tier)) die("--tier is light, standard or heavy");
  const root = process.cwd();
  const pdir = path.join(root, "packs", pack);
  if (!fs.existsSync(path.join(pdir, "pack.json")))
    die(`no packs/${pack}/pack.json here — run new-skill from the root of a skilldrop catalog`);
  for (const p of fs.readdirSync(path.join(root, "packs")))
    if (fs.existsSync(path.join(root, "packs", p, "skills", name))) die(`packs/${p}/skills/${name} already exists`);
  const dir = path.join(pdir, "skills", name);
  const desc = `TODO: one sentence, use-case-first — what it produces. Use when the user asks for …`;
  const files = {
    "SKILL.md": `---\nname: ${name}\ndescription: ${desc}\n---\n\n# ${name}\n\nTODO: one paragraph — what you produce and for whom.\n\n` +
      `## How to respond\n\n1. **Ask for what's missing in one message.** TODO: the inputs, with defaults.\n2. TODO: the steps.\n3. TODO: the output, and how the user checks it.\n\n` +
      `**Non-interactive runs** (subagent, CI, headless): TODO — what to assume, and when to emit \`BLOCKED: <what is missing>\`.\n\n` +
      `## Quality bar\n\n- TODO: a checkable property of a good output\n\n## When to use this skill\n\n- ✅ TODO\n\n` +
      `## When NOT to use this skill\n\n- ❌ TODO; use \`<sibling-skill>\`\n\n## Anti-patterns to avoid\n\n- ❌ **TODO** — and why it fails\n`,
    "manifest.json": JSON.stringify({
      name, version: "0.1.0", description: desc, entrypoint: "SKILL.md",
      deps: { npm: [], pip: [] }, env: { required: [], optional: [] }, related: [], tags: ["todo"],
      model: { tier, rationale: "TODO: why this tier — how much reasoning the task needs" },
    }, null, 2) + "\n",
    "evals/evals.json": JSON.stringify({ skill_name: name, evals: [{ id: 1,
      prompt: "TODO: a realistic request with concrete details",
      assertions: ["TODO: a property the output must have, checkable by reading it"] }] }, null, 2) + "\n",
    "evals/eval_queries.json": "[\n" + [
      { query: "TODO: a phrasing that should trigger this skill", should_trigger: true },
      { query: "TODO: a near-miss that belongs to a sibling skill", should_trigger: false },
    ].map((r) => "  " + JSON.stringify(r)).join(",\n") + "\n]\n",
  };
  if (args.flags["dry-run"]) {
    for (const f of Object.keys(files)) console.log(`would write ${path.relative(root, path.join(dir, f))}`);
    return console.log(`would add ${name} (tier ${tier}) to model-routing.json`);
  }
  for (const [f, body] of Object.entries(files)) {
    fs.mkdirSync(path.dirname(path.join(dir, f)), { recursive: true });
    fs.writeFileSync(path.join(dir, f), body);
    console.log(`wrote ${path.relative(root, path.join(dir, f))}`);
  }
  const rp = path.join(root, "model-routing.json");
  const routingRaw = readIfPresent(rp, null);  // read-and-handle, not check-then-read
  if (routingRaw !== null) {
    const routing = JSON.parse(routingRaw);
    routing.skills = routing.skills || {};
    routing.skills[name] = { tier, rationale: "TODO: why this tier" };
    routing.skills = Object.fromEntries(Object.entries(routing.skills).sort(([a], [b]) => a.localeCompare(b)));
    fs.writeFileSync(rp, JSON.stringify(routing, null, 2) + "\n");
    console.log(`added ${name} to model-routing.json (tier ${tier})`);
  }
  console.log(`\nNext:\n  1. Replace every TODO — the description in SKILL.md and manifest.json must match.` +
              `\n  2. Add ${name} to an outcome in catalogue.json, and a row in guides/reference/skill-catalogue.md.` +
              `\n  3. python3 build_marketplace.py && python3 build_llms.py, then python3 validate.py — it lists what's left.` +
              `\n  4. Try it from another repo: skilldrop install ${name} --from ${root} --local`);
}

/* loop-stats: summarise the opt-in run log loops append to when SKILLDROP_LOOP_LOG is set.
   Local only — the file is the user's, nothing is sent anywhere. Answers the questions a team
   asks of its loops: which gates pass first time, which keep looping back, which block. */
function loopStats(args) {
  const file = args._[0] || process.env.SKILLDROP_LOOP_LOG || path.join(".skilldrop", "loop-log.jsonl");
  const raw = readIfPresent(file, null);
  if (raw === null)
    die(`no run log at ${file}.\n       Turn it on: export SKILLDROP_LOOP_LOG="$PWD/.skilldrop/loop-log.jsonl" — each loop then appends one line per gate verdict.`);
  const days = Number(args.flags.days) || 0;
  const since = days ? Date.now() - days * 864e5 : 0;
  const rows = [], bad = [];
  raw.split(/\r?\n/).forEach((line, i) => {
    if (!line.trim()) return;
    try {
      const r = JSON.parse(line);
      if (!r.loop || !r.verdict) throw new Error("missing loop or verdict");
      if (since && Date.parse(r.ts) < since) return;
      rows.push(r);
    } catch (e) { bad.push(i + 1); }
  });
  const terms = (() => { try { return readJSON(path.join(ROOT, "contracts", "terminals.json")); } catch (e) { return {}; } })();
  // Verdict classes come from the shared vocabulary (RFC-0028), so a new verdict word is
  // classified the same way here as in the loops.
  const classOf = (v) => ((terms.verdicts || {})[v] || {}).class || (/BLOCK/.test(v) ? "blocked" : "unknown");
  const by = {};
  for (const r of rows) {
    const k = `${r.loop}  ${r.gate || "-"} (${r.stage || "?"})`;
    const g = by[k] = by[k] || { n: 0, verdicts: {}, firstPass: 0, firsts: 0, blocked: 0, rounds: [] };
    g.n++; g.verdicts[r.verdict] = (g.verdicts[r.verdict] || 0) + 1;
    const cls = classOf(r.verdict);
    if (Number(r.round) === 1) { g.firsts++; if (cls === "pass" || cls === "conditional") g.firstPass++; }
    if (cls === "blocked") g.blocked++;
    if (r.round) g.rounds.push(Number(r.round));
  }
  if (args.flags.json) return emitJSON({ file, entries: rows.length, skipped: bad.length, gates: by });
  console.log(`${rows.length} gate verdict(s) in ${file}${days ? ` from the last ${days} days` : ""}\n`);
  for (const [k, g] of Object.entries(by).sort()) {
    const mix = Object.entries(g.verdicts).sort((a, b) => b[1] - a[1]).map(([v, n]) => `${v} ${n}`).join(", ");
    const fp = g.firsts ? `${Math.round(100 * g.firstPass / g.firsts)}% pass first time` : "no first-round entries";
    const maxRound = g.rounds.length ? Math.max(...g.rounds) : 0;
    console.log(`${k}\n  ${g.n} verdict(s): ${mix}\n  ${fp} · ${g.blocked} blocked · longest run ${maxRound} round(s)`);
  }
  if (bad.length) console.log(`\n${bad.length} line(s) skipped as unreadable: ${bad.slice(0, 10).join(", ")}${bad.length > 10 ? "…" : ""}`);
}

/* init-catalogue <dir>: start a private catalogue (an internal mirror or a team's own skills)
   in the layout this CLI reads, with one example skill that passes `skilldrop validate`. */
function initCatalogue(args) {
  const dir = path.resolve(args._[0] || die("usage: skilldrop init-catalogue <dir> [--pack <name>]"));
  const pack = args.flags.pack || "team";
  if (!/^[a-z][a-z0-9-]*$/.test(pack)) die(`--pack '${pack}' isn't kebab-case`);
  if (fs.existsSync(dir) && fs.readdirSync(dir).length) die(`${dir} isn't empty — pick a new folder`);
  const sk = "example-skill";
  const files = {
    "catalogue.json": JSON.stringify({ version: "0.1.0", packs: [pack] }, null, 2) + "\n",
    [`packs/${pack}/pack.json`]: JSON.stringify({ description: `Skills for the ${pack} team.`, display_name: pack }, null, 2) + "\n",
    [`packs/${pack}/skills/${sk}/SKILL.md`]: `---\nname: ${sk}\ndescription: Replace with one sentence on what this skill produces. Use when the user asks for …\n---\n\n# ${sk}\n\n` +
      `## How to respond\n\n1. Ask for what's missing in one message.\n2. Do the work.\n3. Say how to check it.\n\n## Quality bar\n\n- A checkable property of a good result\n\n## Anti-patterns to avoid\n\n- ❌ The most common way this goes wrong\n`,
    [`packs/${pack}/skills/${sk}/manifest.json`]: JSON.stringify({ name: sk, version: "0.1.0",
      description: "Replace with one sentence on what this skill produces. Use when the user asks for …",
      entrypoint: "SKILL.md", deps: { npm: [], pip: [] }, env: { required: [], optional: [] }, related: [], tags: ["example"],
      model: { tier: "standard", rationale: "Replace: how much reasoning the task needs." } }, null, 2) + "\n",
    "README.md": `# Skills catalogue\n\nInstall from it with the skilldrop CLI:\n\n\`\`\`bash\nnpx skilldrop-cli list --from <this repo's git URL>\nnpx skilldrop-cli install --pack ${pack} --from <this repo's git URL>#<tag>\n\`\`\`\n\n` +
      `Pin a tag: a branch can change under you. Add a skill with \`npx skilldrop-cli new-skill <name> --pack ${pack}\` from this folder.\n` +
      `Check the catalogue with \`npx skilldrop-cli validate --from .\` (CI runs it on every pull request).\n`,
    ".github/workflows/validate.yml": `name: validate\non: [push, pull_request]\npermissions:\n  contents: read\njobs:\n  validate:\n    runs-on: ubuntu-latest\n    steps:\n` +
      `      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1\n        with:\n          persist-credentials: false\n` +
      `      - run: npx --yes skilldrop-cli@${readJSON(path.join(ROOT, "package.json")).version} validate --from .\n      - run: npx --yes skilldrop-cli@${readJSON(path.join(ROOT, "package.json")).version} scan --from .\n`,
  };
  for (const [rel, body] of Object.entries(files)) {
    fs.mkdirSync(path.dirname(path.join(dir, rel)), { recursive: true });
    fs.writeFileSync(path.join(dir, rel), body);
    console.log(`wrote ${path.relative(process.cwd(), path.join(dir, rel))}`);
  }
  console.log(`\nNext: push ${path.basename(dir)} to your git host, then: npx skilldrop-cli install --pack ${pack} --from <git-url>#<tag>`);
  console.log(`To mirror skills from this catalogue instead, use: skilldrop package <dir> --pack <name>`);
}

/* package <out-dir>: copy a vetted subset of a catalogue into a standalone catalogue an
   organisation can host internally (an air-gapped or reviewed mirror). Packs bring the packs
   they require; loops come only when every stage skill is included. MIRROR.json records where
   each file came from and its SHA-256, so a reviewer can tell exactly what was mirrored. */
function packageCatalogue(args) {
  const out = path.resolve(args._[0] || die("usage: skilldrop package <out-dir> [--pack a,b] [--skills x,y] [--from <src>] [--agents]"));
  if (fs.existsSync(out) && fs.readdirSync(out).length) die(`${out} isn't empty — pick a new folder`);
  const cat = resolveCatalog(args.flags.from);
  if (cat.shape === "apm") die("package reads skilldrop catalogues; agentbundle ones aren't supported yet");
  const ps = packsOf(cat) || {};
  let packNames = args.flags.pack && args.flags.pack !== true ? String(args.flags.pack).split(",") : [];
  for (const p of packNames) if (!ps[p]) die(`unknown pack '${p}' in catalog '${cat.source}'`);
  for (const p of packNames.slice()) for (const r of ps[p].requires || []) if (!packNames.includes(r)) packNames.unshift(r);
  let skills = [];
  for (const p of packNames) for (const s of ps[p].skills || []) if (!skills.includes(s)) skills.push(s);
  if (args.flags.skills) for (const s of String(args.flags.skills).split(",")) {
    if (!skillExists(cat, s)) die(`unknown skill '${s}' in catalog '${cat.source}'`);
    if (!skills.includes(s)) skills.push(s);
  }
  if (!packNames.length && !args.flags.skills) { skills = skillsIn(cat); packNames = Object.keys(ps); }
  gate(cat, skills);
  const home = (s) => Object.keys(ps).find((p) => (ps[p].skills || []).includes(s)) || "mirror";
  const manifest = { source: cat.source, cli: readJSON(path.join(ROOT, "package.json")).version,
                     created: new Date().toISOString(), files: {} };
  const copyTree = (src, dstRel) => {
    for (const f of walkFiles(src)) {
      const rel = path.join(dstRel, path.relative(src, f)).split(path.sep).join("/");
      fs.mkdirSync(path.dirname(path.join(out, rel)), { recursive: true });
      fs.copyFileSync(f, path.join(out, rel));
      manifest.files[rel] = sha256(fs.readFileSync(f));
    }
  };
  const usedPacks = [];
  for (const s of skills) {
    const p = home(s);
    if (!usedPacks.includes(p)) usedPacks.push(p);
    copyTree(skillDir(cat, s), path.join("packs", p, "skills", s));
  }
  const loops = [];
  for (const l of loopsIn(cat)) {
    if (loopSkills(cat, l).every((s) => skills.includes(s))) {
      const p = Object.keys(ps).find((x) => (ps[x].loops || []).includes(l)) || usedPacks[0];
      if (!usedPacks.includes(p)) continue;
      copyTree(loopDir(cat, l), path.join("packs", p, "loops", l));
      loops.push(l);
    }
  }
  for (const p of usedPacks) {
    const meta = Object.assign({}, ps[p] || { description: "Mirrored skills." });
    delete meta.skills; delete meta.loops;
    if (meta.requires) meta.requires = meta.requires.filter((r) => usedPacks.includes(r));
    if (meta.journey) meta.journey.steps = (meta.journey.steps || []).filter((st) => skills.includes(st.skill));
    const rel = `packs/${p}/pack.json`;
    fs.mkdirSync(path.dirname(path.join(out, rel)), { recursive: true });
    fs.writeFileSync(path.join(out, rel), JSON.stringify(meta, null, 2) + "\n");
  }
  fs.writeFileSync(path.join(out, "catalogue.json"), JSON.stringify({ version: "0.1.0", packs: usedPacks }, null, 2) + "\n");
  let agents = [];
  if (args.flags.agents) for (const a of agentsIn(cat)) { copyTree(path.dirname(agentPath(cat, a)), "agents"); agents = agentsIn(cat); break; }
  fs.writeFileSync(path.join(out, "MIRROR.json"), JSON.stringify(manifest, null, 2) + "\n");
  console.log(`packaged ${skills.length} skill(s), ${loops.length} loop(s)${agents.length ? `, ${agents.length} agent(s)` : ""} in ${usedPacks.length} pack(s) from '${cat.source}' -> ${out}`);
  console.log(`MIRROR.json records the source and a SHA-256 for each of the ${Object.keys(manifest.files).length} files.`);
  console.log(`Next: review it, push it to your internal git host, then: npx skilldrop-cli install --pack <name> --from <internal-git-url>#<tag>`);
}

function listAgents(args) {
  const cat = resolveCatalog(args.flags.from);
  const names = agentsIn(cat);
  if (args.flags.json)
    return emitJSON({
      catalog: cat.source,
      count: names.length,
      agents: names.map((a) => {
        const m = agentMeta(cat, a);
        return { name: a, description: m.description || null, tools: m.tools || null, model: m.model || null };
      }),
    });
  if (!names.length) return console.log(`catalog '${cat.source}' ships no agents.`);
  const w = Math.max(...names.map((n) => n.length));
  for (const a of names) {
    const m = agentMeta(cat, a);
    console.log(`${a.padEnd(w)}  ${m.description}`);
  }
  console.log(`\n${names.length} agent(s). Install one: skilldrop install --agent <name>`);
}

/* Loops (RFC-0028): an ordered sequence of stages over existing skills, with a gate between
   them. LOOP.md's frontmatter is already SKILL.md's shape (name + description), so a loop
   projects into the target's skill directory as <name>/SKILL.md and becomes invokable exactly
   like a skill. loop.json travels beside it so stages, gates and cap stay machine-readable
   after install. A loop never contains a skill — installing one also installs the skills its
   stages name, unless --no-skills. Optional in a catalog. */
function loopsIn(cat) {
  if (cat.shape === "apm") return [];
  if (cat.loopIndex) return Object.keys(cat.loopIndex).sort();
  const d = path.join(cat.dir, "loops");
  if (!fs.existsSync(d)) return [];
  return fs.readdirSync(d).filter((x) => fs.existsSync(path.join(d, x, "loop.json"))).sort();
}
function loopDir(cat, n) { return cat.loopIndex ? cat.loopIndex[n] : path.join(cat.dir, "loops", n); }
function loopSpec(cat, n) { return readJSON(path.join(loopDir(cat, n), "loop.json")); }

function loopSkills(cat, n) {
  const seen = [];
  for (const st of loopSpec(cat, n).stages || [])
    for (const sk of st.skills || [])
      if (sk !== "*" && !seen.includes(sk)) seen.push(sk);
  return seen;
}

function checkLoop(cat, n) {
  const problems = [];
  if (!fs.existsSync(path.join(loopDir(cat, n), "LOOP.md"))) problems.push("no LOOP.md — it is the entrypoint");
  let spec;
  try { spec = loopSpec(cat, n); } catch (e) { return problems.concat("loop.json is missing or unparseable"); }
  if (spec.name !== n) problems.push(`loop.json name '${spec.name}' != folder '${n}'`);
  if (!Array.isArray(spec.stages) || !spec.stages.length) problems.push("no stages — a loop with none sequences nothing");
  for (const sk of loopSkills(cat, n))
    if (!skillExists(cat, sk)) problems.push(`stage names skill '${sk}', which is not in this catalog`);
  return problems;
}

function listLoops(args) {
  const cat = resolveCatalog(args.flags.from);
  const names = loopsIn(cat);
  if (args.flags.json)
    return emitJSON({
      catalog: cat.source, count: names.length,
      loops: names.map((n) => {
        const sp = loopSpec(cat, n);
        return { name: n, kind: sp.kind, cap: sp.cap ?? 3, description: sp.description,
                 stages: (sp.stages || []).map((st) => ({ id: st.id, type: st.type, skills: st.skills,
                   gate: st.gate ? { id: st.gate.id, kind: st.gate.kind } : null })) };
      }),
    });
  if (!names.length) return console.log(`catalog '${cat.source}' ships no loops.`);
  for (const n of names) {
    const sp = loopSpec(cat, n);
    const gates = (sp.stages || []).filter((st) => st.gate).map((st) => `${st.gate.id}:${st.gate.kind}`);
    console.log(`${n}  [${sp.kind}, cap ${sp.cap ?? 3}]`);
    console.log(`  ${(sp.stages || []).map((st) => st.id).join(" -> ")}`);
    console.log(`  gates: ${gates.join(", ") || "none"}`);
  }
  console.log(`\n${names.length} loop(s). Install one: skilldrop install --loop <name>`);
}

function installLoops(args) {
  const cat = resolveCatalog(args.flags.from);
  const available = loopsIn(cat);
  if (!available.length) die(`catalog '${cat.source}' ships no loops`);
  let names = args._.slice();
  if (!names.length && args.flags.pack) {
    const ps = packsOf(cat);
    if (!ps) die(`catalog '${cat.source}' defines no packs`);
    packAlias(args.flags, ps);
    const pk = ps[args.flags.pack];
    if (!pk) die(`unknown pack '${args.flags.pack}' in catalog '${cat.source}'`);
    names = packMembers(ps, args.flags.pack, "loops");
    if (!names.length) die(`pack '${args.flags.pack}' declares no loops`);
  }
  if (!names.length && args.flags.all) names = available.slice();
  if (!names.length) die("nothing to install — pass loop names, --pack <name>, or --all");
  for (const n of names) if (!available.includes(n)) die(`unknown loop '${n}' in catalog '${cat.source}'`);

  let bad = 0;
  for (const n of names) {
    const problems = checkLoop(cat, n);
    for (const pr of problems) console.error(`refused ${n}: ${pr}`);
    if (problems.length) bad++;
  }
  if (bad) die(`${bad} loop(s) failed the structural check — nothing was installed`);

  const { dest, ide } = target(args.flags);
  fs.mkdirSync(dest, { recursive: true });
  const l = ledger(dest);
  const notes = [];
  for (const n of names) {
    const sp = loopSpec(cat, n);
    const out = path.join(dest, n);
    fs.mkdirSync(out, { recursive: true });
    fs.copyFileSync(path.join(loopDir(cat, n), "LOOP.md"), path.join(out, "SKILL.md"));
    fs.copyFileSync(path.join(loopDir(cat, n), "loop.json"), path.join(out, "loop.json"));
    const note = writeWiring(ide, dest, n, sp.description);
    if (note) notes.push(note);
    l.data[n] = { version: sp.version || null, source: cat.source, loop: true };
    console.log(`installed loop ${n} -> ${out}`);
  }
  saveLedger(l);
  if (args.flags.local) addLocal(dest, ide, names);

  const wanted = [];
  for (const n of names) for (const sk of loopSkills(cat, n)) if (!wanted.includes(sk)) wanted.push(sk);
  if (args.flags["no-skills"]) {
    console.log(`\n${names.length} loop(s) installed (${ide}). Skipped ${wanted.length} stage skill(s) (--no-skills).`);
    console.log(`A loop whose stage skills are absent still runs — each stage degrades via its declared fallback.`);
  } else if (wanted.length) {
    console.log(`\nInstalling ${wanted.length} stage skill(s) the loop sequences.\n`);
    const flags = Object.assign({}, args.flags);
    delete flags.loop; delete flags.pack; delete flags.all;
    install({ _: wanted, flags });
  }
  if (notes.length) console.log(`\n${notes.join("\n")}`);
  console.log(`\nRun a loop by name — e.g. "run the ${names[0]} loop on this". Its SKILL.md is the script; honour each gate and the cap.`);
}

function uninstallLoops(args) {
  if (!args._.length) die("pass loop names to uninstall");
  const { dest, ide } = target(args.flags);
  const l = ledger(dest);
  if (args.flags["dry-run"]) {
    for (const n of args._) console.log(`would remove loop ${path.join(dest, n)} (stage skills left in place)`);
    return;
  }
  if (!confirm(`Remove ${args._.length} loop(s) from ${dest}: ${args._.join(", ")}?`, args.flags)) return console.log("cancelled — nothing removed.");
  for (const n of args._) {
    fs.rmSync(path.join(dest, n), { recursive: true, force: true });
    const w = wiringPath(ide, dest, n);
    if (w) fs.rmSync(w, { force: true });
    delete l.data[n];
    console.log(`removed loop ${n} from ${dest} (stage skills left in place)`);
  }
  saveLedger(l);
  removeLocal(dest, ide, args._);
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
  const warns = [];
  for (const a of names) {
    const { file, warn } = writeAgent(cat, a, dest, ide);
    if (warn) warns.push(warn);
    l.data[a] = { version: null, source: cat.source, file }; // agents carry no version yet (RFC-0012)
    console.log(`installed ${a} -> ${path.join(dest, file)}`);
  }
  saveLedger(l);
  console.log(`\n${names.length} agent(s) installed (${ide}).`);
  if (warns.length) console.log(`\nTool mapping:\n${warns.join("\n")}`);
  if (ide === "claude") console.log("Delegate by name, e.g. \"use the devils-advocate agent on this diff\".");
  if (ide === "kiro") console.log("Kiro grants `tools` but not auto-approval — you are prompted per call by design.");
  if (ide === "copilot") console.log("Invoke with: copilot --agent <name>");
  if (ide === "codex") console.log("sandbox_mode is left unset, so each agent inherits the parent session's permissions.");
  if (ide === "antigravity") console.log("Emitted with `subagent: true` so invoke_subagent can reach them.");
  if (cat.source !== BUNDLED)
    console.log(`\nWARNING: third-party catalog '${cat.source}'. An agent is a system prompt your tool will adopt — read it before first use. Install copied files only; nothing was executed.`);
}

function uninstallAgents(args) {
  if (!args._.length) die("pass agent names to uninstall");
  const { dest } = agentTarget(args.flags);
  const l = ledger(dest);
  if (args.flags["dry-run"]) {
    for (const a of args._) console.log(`would remove agent ${a} from ${dest}`);
    return;
  }
  if (!confirm(`Remove ${args._.length} agent(s) from ${dest}: ${args._.join(", ")}?`, args.flags)) return console.log("cancelled — nothing removed.");
  for (const a of args._) {
    const rec = l.data[a];
    for (const f of new Set([rec && rec.file, `${a}.md`, `${a}.json`, `${a}.agent.md`, `${a}.toml`].filter(Boolean)))
      fs.rmSync(path.join(dest, f), { force: true });
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
  if (args.flags.json)
    return emitJSON({
      catalog: cat.source,
      count: rows.length,
      skills: rows.map(([name, version, tier]) => ({ name, version, tier })),
    });
  const w = Math.max(...rows.map((r) => r[0].length));
  for (const [s, v, t] of rows) console.log(`${s.padEnd(w)}  ${v}  ${t}`);
  console.log(`\n${rows.length} skills in catalog '${cat.source}'. Details: skilldrop info <skill>`);
}

/* RFC-0032: what to try first after installing a pack, how to tell it worked, what to do
   if it didn't — the same first-value block the pack's site page renders. */
function firstValueLines(p) {
  const fv = p["first-value"];
  if (!fv) return [];
  const out = [`Start here: ${fv["starter-task"]}`, "", `  ${fv["starter-prompt"]}`, ""];
  for (const pre of fv.prerequisites || []) out.push(`  before you start: ${pre}`);
  out.push(`  worked if: ${fv.verification}`, `  if nothing happens: ${fv.recovery}`);
  return out;
}

function infoPack(args) {
  const cat = resolveCatalog(args.flags.from);
  const ps = packsOf(cat) || die(`catalog '${cat.source}' has no packs`);
  packAlias(args.flags, ps);
  const name = args.flags.pack;
  const p = ps[name] || die(`unknown pack '${name}' — available: ${Object.keys(ps).join(", ")}`);
  if (args.flags.json)
    return emitJSON({ catalog: cat.source, name, ...p });
  console.log(`${p.display_name || name}  (${name})\n\n${p.description}\n`);
  console.log(`skills:   ${p.skills.join(", ")}`);
  if ((p.requires || []).length) console.log(`requires: ${p.requires.join(", ")} (installed with it)`);
  if ((p.loops || []).length) console.log(`loops:    ${p.loops.join(", ")}`);
  if (p.links && p.links.documentation) console.log(`page:     ${p.links.documentation}`);
  const fv = firstValueLines(p);
  if (fv.length) console.log("\n" + fv.join("\n"));
}

function info(args) {
  if (args.flags.pack) return infoPack(args);
  const cat = resolveCatalog(args.flags.from);
  const s = args._[0] || die("pass a skill name, or --pack <name>");
  if (!skillExists(cat, s)) die(`unknown skill '${s}' in catalog '${cat.source}'`);
  const m = manifestOf(cat, s);
  const ps = packsOf(cat) || {};
  const inPacks = Object.entries(ps).filter(([, p]) => p.skills.includes(s)).map(([n]) => n);
  const needsPip = ((m.deps || {}).pip || []).length > 0 || fs.existsSync(path.join(skillDir(cat, s), "requirements.txt"));
  if (args.flags.json)
    return emitJSON({
      catalog: cat.source,
      name: m.name,
      version: m.version || null,
      description: m.description || null,
      tier: (m.model && m.model.tier) || null,
      packs: inPacks,
      related: m.related || [],
      tags: m.tags || [],
      deps: { pip: (m.deps || {}).pip || [], npm: (m.deps || {}).npm || [], requirementsTxt: needsPip },
      env: { required: (m.env || {}).required || [], optional: (m.env || {}).optional || [] },
      hooks: m.hooks || [],
      permissions: m.permissions || null,
    });
  console.log(`${m.name}@${m.version}  (tier: ${(m.model && m.model.tier) || "n/a"})\n\n${m.description}\n`);
  console.log(`catalog: ${cat.source}`);
  console.log(`packs:   ${inPacks.join(", ") || "-"}`);
  console.log(`related: ${(m.related || []).join(", ") || "-"}`);
  if (((m.deps || {}).pip || []).length || fs.existsSync(path.join(skillDir(cat, s), "requirements.txt")))
    console.log("deps:    python (requirements.txt)");
  if (((m.env || {}).required || []).length) console.log(`env:     ${m.env.required.join(", ")} (required)`);
  if (fs.existsSync(path.join(skillDir(cat, s), "scripts")))
    console.log(`scripts: ${permissionSummary(m.permissions)}${m.permissions && m.permissions.notes ? `\n         ${m.permissions.notes}` : ""}`);
}

function listPacks(args) {
  const cat = resolveCatalog(args.flags.from);
  const ps = packsOf(cat);
  if (args.flags.json)
    return emitJSON({
      catalog: cat.source,
      count: ps ? Object.keys(ps).length : 0,
      packs: Object.entries(ps || {}).map(([name, p]) => ({
        name, description: p.description || null, skills: p.skills || [], requires: p.requires || [],
      })),
    });
  if (!ps) return console.log(`catalog '${cat.source}' defines no packs.`);
  const w = Math.max(...Object.keys(ps).map((n) => n.length));
  for (const [n, p] of Object.entries(ps))
    console.log(`${n.padEnd(w)}  (${p.skills.length} skills${(p.requires || []).length ? ` + ${p.requires.join(", ")}` : ""})  ${p.description}`);
  console.log("\nInstall one: skilldrop install --pack <name>");
}

function validateCmd(args) {
  const cat = resolveCatalog(args.flags.from);
  const names = skillsIn(cat);
  let bad = 0;
  for (const s of names) {
    const problems = checkSkill(cat, s);
    for (const f of scanSkill(cat, s).filter((x) => x.id.startsWith("undeclared-")))
      problems.push(`${f.file}:${f.line} ${f.why} (RFC-0039)`);
    for (const p of problems) console.log(`FAIL ${s}: ${p}`);
    if (problems.length) bad++;
  }
  const ps = packsOf(cat);
  if (ps)
    for (const [n, p] of Object.entries(ps))
      for (const s of p.skills)
        if (!names.includes(s)) { console.log(`FAIL packs: pack '${n}' lists unknown skill '${s}'`); bad++; }
  if (bad) { console.log(`\n${bad} problem(s) in catalog '${cat.source}'.`); process.exit(1); }
  console.log(`OK: ${names.length} skills in catalog '${cat.source}' pass the structural check.`);
}

/* ---------- bootstrap (enterprise distribution) ----------
   Writes the skilldrop marketplace into ~/.claude/settings.json so every Claude Code
   session on this machine discovers the catalogue without any per-session /plugin command.
   Idempotent: safe to run in a provisioning script or onboarding runbook. */
const BOOTSTRAP_MARKETPLACE_KEY = "skilldrop";
const BOOTSTRAP_GITHUB_OWNER = "sananthanarayan";
const BOOTSTRAP_GITHUB_REPO = "skilldrop";

function bootstrap() {
  const settingsPath = path.join(os.homedir(), ".claude", "settings.json");
  let data = {};
  const raw = readIfPresent(settingsPath, null);
  if (raw !== null) {
    try { data = JSON.parse(raw); }
    catch (e) { die(`${settingsPath} is not valid JSON — fix it first, then re-run bootstrap`); }
  }
  data.extraKnownMarketplaces = data.extraKnownMarketplaces || {};
  const entry = { source: { source: "github", owner: BOOTSTRAP_GITHUB_OWNER, repo: BOOTSTRAP_GITHUB_REPO } };
  const existing = data.extraKnownMarketplaces[BOOTSTRAP_MARKETPLACE_KEY];
  if (existing && JSON.stringify(existing) === JSON.stringify(entry)) {
    console.log(`already configured: ${BOOTSTRAP_MARKETPLACE_KEY} -> github:${BOOTSTRAP_GITHUB_OWNER}/${BOOTSTRAP_GITHUB_REPO}`);
    console.log(`\nIn any Claude Code session:\n  /plugin install <pack>@${BOOTSTRAP_MARKETPLACE_KEY}`);
    return;
  }
  data.extraKnownMarketplaces[BOOTSTRAP_MARKETPLACE_KEY] = entry;
  fs.mkdirSync(path.dirname(settingsPath), { recursive: true });
  fs.writeFileSync(settingsPath, JSON.stringify(data, null, 2) + "\n");
  console.log(`configured ${settingsPath}:`);
  console.log(`  extraKnownMarketplaces.${BOOTSTRAP_MARKETPLACE_KEY} -> github:${BOOTSTRAP_GITHUB_OWNER}/${BOOTSTRAP_GITHUB_REPO}`);
  console.log(`\nIn any Claude Code session, install a role pack:\n  /plugin install solution-architect@${BOOTSTRAP_MARKETPLACE_KEY}`);
  console.log(`  /plugin install dev-team@${BOOTSTRAP_MARKETPLACE_KEY}`);
  console.log(`  /plugin install ai-engineering@${BOOTSTRAP_MARKETPLACE_KEY}`);
  console.log(`\nOr install the full catalogue:\n  /plugin install ${BOOTSTRAP_MARKETPLACE_KEY}@${BOOTSTRAP_MARKETPLACE_KEY}`);
}

const args = parseArgs(process.argv.slice(2));
const cmd = args._.shift();
const commands = { list, info, packs: listPacks, profiles: listProfiles, agents: listAgents, loops: listLoops, install, update, outdated, uninstall, diff, doctor, "new-skill": newSkill, "loop-stats": loopStats, "init-catalogue": initCatalogue, package: packageCatalogue, validate: validateCmd, scan, bootstrap };
if (args.flags.version || cmd === "version") console.log(readJSON(path.join(ROOT, "package.json")).version);
else if (!cmd || cmd === "help" || args.flags.help) console.log(HELP);
else if (commands[cmd]) commands[cmd](args);
else die(`unknown command '${cmd}' — run: skilldrop help`);

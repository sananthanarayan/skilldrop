#!/usr/bin/env node
/* skilldrop — install portable AI-agent skills into Claude Code, Cursor, Kiro,
 * or any directory. Zero dependencies; skills ship inside this package.
 * Design: skilldrop-cli-design/skilldrop-cli-design.md · Scope: docs/rfcs/0002-skilldrop-cli.md
 */
"use strict";
const fs = require("fs");
const path = require("path");
const os = require("os");

const ROOT = path.resolve(__dirname, "..");
const SKILLS = path.join(ROOT, "skills");
const LEDGER = ".skilldrop.json";

const HELP = `skilldrop — portable AI-agent skills for Claude Code, Cursor, Kiro, and more

Usage:
  skilldrop list                          all skills (name, version, tier)
  skilldrop info <skill>                  description, related, packs, deps
  skilldrop packs                         role-based packs
  skilldrop install <skill...>            install skills (default: Claude Code, user scope)
  skilldrop install --pack <name>         install a whole pack
  skilldrop install --all                 install every skill
  skilldrop update                        re-copy installed skills whose version changed
  skilldrop outdated                      show installed vs current versions, change nothing
  skilldrop uninstall <skill...>          remove skills (and wiring files this tool wrote)

Install/update/uninstall targets (pick one):
  (default)          ~/.claude/skills           Claude Code, user scope
  --project          ./.claude/skills           Claude Code, project scope
  --ide cursor       ./.cursor/skills           + writes .cursor/rules/<skill>.mdc
  --ide kiro         ./.kiro/skills             + writes .kiro/steering/<skill>.md
  --dest <dir>       any directory              Codex / Continue / Cline / Aider (wiring tips printed)

Options:
  --with-related     also install each skill's related companions (one level)
`;

function die(msg) { console.error("error: " + msg); process.exit(1); }
function readJSON(p) { return JSON.parse(fs.readFileSync(p, "utf8")); }
function allSkills() {
  return fs.readdirSync(SKILLS).filter((d) => fs.statSync(path.join(SKILLS, d)).isDirectory()).sort();
}
function manifest(s) { return readJSON(path.join(SKILLS, s, "manifest.json")); }
function packs() { return readJSON(path.join(ROOT, "packs.json")).packs; }

function parseArgs(argv) {
  const out = { _: [], flags: {} };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--pack" || a === "--ide" || a === "--dest") out.flags[a.slice(2)] = argv[++i];
    else if (a.startsWith("--")) out.flags[a.slice(2)] = true;
    else out._.push(a);
  }
  return out;
}

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

function ledger(dest) {
  const p = path.join(dest, LEDGER);
  return { path: p, data: fs.existsSync(p) ? readJSON(p) : {} };
}
function saveLedger(l) { fs.writeFileSync(l.path, JSON.stringify(l.data, null, 2) + "\n"); }

function wiringPath(ide, dest, s) {
  const base = path.dirname(dest); // .cursor/ or .kiro/
  if (ide === "cursor") return path.join(base, "rules", `${s}.mdc`);
  if (ide === "kiro") return path.join(base, "steering", `${s}.md`);
  return null;
}
function writeWiring(ide, dest, s, desc) {
  const p = wiringPath(ide, dest, s);
  if (!p) return;
  fs.mkdirSync(path.dirname(p), { recursive: true });
  if (ide === "cursor")
    fs.writeFileSync(p, `---\ndescription: ${desc.replace(/\n/g, " ")}\nglobs:\nalwaysApply: false\n---\nFollow the instructions in .cursor/skills/${s}/SKILL.md when the user requests this task.\n`);
  else
    fs.writeFileSync(p, `When the user requests the following, defer to the instructions in .kiro/skills/${s}/SKILL.md:\n\n${desc}\n`);
}

function expandNames(args) {
  if (args.flags.all) return allSkills();
  if (args.flags.pack) {
    const p = packs()[args.flags.pack];
    if (!p) die(`unknown pack '${args.flags.pack}' — run: skilldrop packs`);
    return p.skills.slice();
  }
  if (!args._.length) die("nothing to install — pass skill names, --pack <name>, or --all");
  for (const s of args._) if (!fs.existsSync(path.join(SKILLS, s))) die(`unknown skill '${s}' — run: skilldrop list`);
  return args._.slice();
}

function install(args) {
  let names = expandNames(args);
  if (args.flags["with-related"]) {
    const seen = new Set(names);
    for (const s of names.slice()) for (const r of manifest(s).related || []) if (!seen.has(r)) { seen.add(r); names.push(r); }
  }
  const { dest, ide } = target(args.flags);
  fs.mkdirSync(dest, { recursive: true });
  const l = ledger(dest);
  const pipDeps = [], suggestions = new Set();
  for (const s of names) {
    const m = manifest(s);
    fs.cpSync(path.join(SKILLS, s), path.join(dest, s), { recursive: true });
    writeWiring(ide, dest, s, m.description);
    l.data[s] = m.version;
    if (fs.existsSync(path.join(SKILLS, s, "requirements.txt"))) pipDeps.push(s);
    for (const r of m.related || []) if (!names.includes(r) && !l.data[r]) suggestions.add(r);
    console.log(`installed ${s}@${m.version} -> ${dest}`);
  }
  saveLedger(l);
  console.log(`\n${names.length} skill(s) installed (${ide}).`);
  if (ide === "generic")
    console.log("wiring: attach each skill's SKILL.md to your agent (Continue/Cline: @file, Aider: /add, Codex: reference it from AGENTS.md) — see the repo README's per-IDE steps.");
  for (const s of pipDeps)
    console.log(`deps: ${s} needs Python packages — run: cd ${path.join(dest, s)} && python3 -m pip install -r requirements.txt`);
  if (suggestions.size)
    console.log(`related (not installed): ${[...suggestions].sort().join(", ")} — add --with-related or install by name.`);
}

function eachInstalled(flags, fn) {
  const { dest, ide } = target(flags);
  const l = ledger(dest);
  const rows = Object.keys(l.data).sort().map((s) => ({
    s, installed: l.data[s],
    current: fs.existsSync(path.join(SKILLS, s)) ? manifest(s).version : null,
  }));
  return fn({ dest, ide, l, rows });
}

function update(args) {
  eachInstalled(args.flags, ({ dest, ide, l, rows }) => {
    if (!rows.length) return console.log(`nothing installed at ${dest}`);
    let n = 0;
    for (const r of rows) {
      if (!r.current) { console.log(`skip ${r.s}: no longer in the catalog`); continue; }
      if (r.current === r.installed) continue;
      fs.cpSync(path.join(SKILLS, r.s), path.join(dest, r.s), { recursive: true });
      writeWiring(ide, dest, r.s, manifest(r.s).description);
      l.data[r.s] = r.current;
      console.log(`updated ${r.s} ${r.installed} -> ${r.current}`);
      n++;
    }
    saveLedger(l);
    console.log(n ? `\n${n} skill(s) updated.` : "everything up to date.");
  });
}

function outdated(args) {
  eachInstalled(args.flags, ({ dest, rows }) => {
    if (!rows.length) return console.log(`nothing installed at ${dest}`);
    const stale = rows.filter((r) => r.current && r.current !== r.installed);
    for (const r of stale) console.log(`${r.s}: installed ${r.installed}, current ${r.current}`);
    console.log(stale.length ? `\n${stale.length} outdated — run: skilldrop update` : "everything up to date.");
  });
}

function uninstall(args) {
  if (!args._.length) die("pass skill names to uninstall");
  const { dest, ide } = target(args.flags);
  const l = ledger(dest);
  for (const s of args._) {
    fs.rmSync(path.join(dest, s), { recursive: true, force: true });
    const w = wiringPath(ide, dest, s);
    if (w) fs.rmSync(w, { force: true });
    delete l.data[s];
    console.log(`removed ${s} from ${dest}`);
  }
  saveLedger(l);
}

function list() {
  const rows = allSkills().map((s) => { const m = manifest(s); return [s, m.version, m.model.tier]; });
  const w = Math.max(...rows.map((r) => r[0].length));
  for (const [s, v, t] of rows) console.log(`${s.padEnd(w)}  ${v}  ${t}`);
  console.log(`\n${rows.length} skills. Details: skilldrop info <skill>`);
}

function info(args) {
  const s = args._[0] || die("pass a skill name");
  if (!fs.existsSync(path.join(SKILLS, s))) die(`unknown skill '${s}'`);
  const m = manifest(s);
  const inPacks = Object.entries(packs()).filter(([, p]) => p.skills.includes(s)).map(([n]) => n);
  console.log(`${m.name}@${m.version}  (tier: ${m.model.tier})\n\n${m.description}\n`);
  console.log(`packs:   ${inPacks.join(", ") || "-"}`);
  console.log(`related: ${(m.related || []).join(", ") || "-"}`);
  if ((m.deps.pip || []).length || fs.existsSync(path.join(SKILLS, s, "requirements.txt")))
    console.log("deps:    python (requirements.txt)");
  if ((m.env.required || []).length) console.log(`env:     ${m.env.required.join(", ")} (required)`);
}

function listPacks() {
  const ps = packs();
  const w = Math.max(...Object.keys(ps).map((n) => n.length));
  for (const [n, p] of Object.entries(ps))
    console.log(`${n.padEnd(w)}  (${p.skills.length} skills)  ${p.description}`);
  console.log("\nInstall one: skilldrop install --pack <name>");
}

const args = parseArgs(process.argv.slice(2));
const cmd = args._.shift();
const commands = { list, info, packs: listPacks, install, update, outdated, uninstall };
if (!cmd || cmd === "help" || args.flags.help) console.log(HELP);
else if (commands[cmd]) commands[cmd](args);
else die(`unknown command '${cmd}' — run: skilldrop help`);

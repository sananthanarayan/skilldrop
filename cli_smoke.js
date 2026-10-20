#!/usr/bin/env node
/* cli_smoke.js — run the CLI the way a user does, on whatever OS this is (RFC-0056).

   Every command is a real `node bin/skilldrop.js …` call in a throwaway folder, with HOME and
   USERPROFILE pointed at a throwaway home so nothing touches the machine's own settings. It
   exists for the Windows job in CI: paths, git calls and file permissions are where a CLI
   written on macOS breaks, and only running it there finds out.

     node cli_smoke.js            # every check; exits 1 if any fails
     node cli_smoke.js search     # only the checks whose name contains "search"

   Zero dependencies, like the CLI. Not part of the published package (package.json `files`). */
"use strict";
const fs = require("fs");
const os = require("os");
const path = require("path");
const { execFileSync, spawnSync } = require("child_process");

const ROOT = __dirname;
const CLI = path.join(ROOT, "bin", "skilldrop.js");
const TMP = fs.mkdtempSync(path.join(os.tmpdir(), "skilldrop-smoke-"));
const HOME = path.join(TMP, "home");
fs.mkdirSync(HOME);
const ENV = Object.assign({}, process.env, { HOME, USERPROFILE: HOME, SKILLDROP_POLICY: "", NO_COLOR: "1" });
delete ENV.SKILLDROP_POLICY;

function run(args, { cwd = TMP, ok = true, env = {} } = {}) {
  const r = spawnSync(process.execPath, [CLI, ...args], { cwd, env: Object.assign({}, ENV, env), encoding: "utf8" });
  const out = (r.stdout || "") + (r.stderr || "");
  if (ok && r.status !== 0) throw new Error(`skilldrop ${args.join(" ")} exited ${r.status}:\n${out.slice(-1500)}`);
  if (!ok && r.status === 0) throw new Error(`skilldrop ${args.join(" ")} should have failed:\n${out.slice(-1500)}`);
  return out;
}
const json = (args, opts) => JSON.parse(run(args, opts));
const dir = (name) => { const d = path.join(TMP, name); fs.mkdirSync(d, { recursive: true }); return d; };
const exists = (...p) => fs.existsSync(path.join(...p));
function expect(cond, why) { if (!cond) throw new Error(why); }
function git(cwd, ...a) { return execFileSync("git", a, { cwd, encoding: "utf8", env: ENV }); }
function gitRepo(name) {
  const d = dir(name);
  git(d, "init", "-q");
  git(d, "config", "user.email", "smoke@example.com");
  git(d, "config", "user.name", "smoke");
  return d;
}
const PY = ["python3", "python"].find((p) => spawnSync(p, ["--version"], { encoding: "utf8" }).status === 0);

const checks = [];
const check = (name, fn) => checks.push({ name, fn });

check("version and help", () => {
  expect(/^\d+\.\d+\.\d+/.test(run(["--version"]).trim()), "--version is not a version");
  expect(run(["--help"]).includes("skilldrop install"), "--help has no install line");
});

check("validate the bundled catalogue", () => {
  expect(run(["validate"]).includes("pass the structural check"), "validate did not pass");
});

check("scan skills and agents", () => {
  const r = json(["scan", "--json"]);
  expect(r.scanned > 90 && r.agentsScanned >= 3, `scanned ${r.scanned} skills and ${r.agentsScanned} agents`);
});

check("list and search", () => {
  const l = json(["list", "--json"]);
  expect(l.count > 90, `list found ${l.count} skills`);
  const s = json(["search", "sql", "review", "--json"]);
  expect(s.results[0] && s.results[0].name === "sql-review", `search "sql review" found ${JSON.stringify(s.results[0])}`);
  const a = json(["search", "security", "--kind", "agent", "--json"]);
  expect(a.results.every((x) => x.kind === "agent") && a.results.length, "search --kind agent returned other kinds");
  run(["search"], { ok: false });
});

check("install, diff, update and uninstall a skill with --dest", () => {
  const d = dir("dest-a");
  run(["install", "sql-review", "--dest", d]);
  expect(exists(d, "sql-review", "SKILL.md") && exists(d, "sql-review", "scripts", "sql_lint.py"), "files not copied");
  const ledger = JSON.parse(fs.readFileSync(path.join(d, ".skilldrop.json"), "utf8"));
  const entry = ledger["sql-review"] || (ledger.skills || {})["sql-review"];
  expect(entry, "ledger has no sql-review entry");
  run(["outdated", "--dest", d]);
  const md = path.join(d, "sql-review", "SKILL.md");
  const original = fs.readFileSync(md, "utf8");
  fs.appendFileSync(md, "\nlocal edit\n");
  expect(run(["diff", "sql-review", "--dest", d]).includes("SKILL.md"), "diff did not name the edited file");
  run(["update", "sql-review", "--dest", d]);  // same version upstream: a local edit is kept
  expect(fs.readFileSync(md, "utf8") !== original, "update overwrote a local edit with no new version");
  run(["uninstall", "sql-review", "--yes", "--dest", d]);
  expect(!exists(d, "sql-review"), "uninstall left the folder");
});

check("the one-time star line never reaches a pipe or CI", () => {
  // spawnSync's stdout is a pipe, as in a script or CI, so the line must not print and no
  // marker may be written (the marker is what would stop it showing at a real terminal later).
  const d = dir("dest-star");
  const out = run(["install", "brief-intake", "--dest", d], { env: { CI: "" } });
  expect(!out.includes("a star helps"), "the star line printed to a pipe");
  expect(!exists(HOME, ".config", "skilldrop", "star-shown"), "a pipe install wrote the star marker");
});

check("install a pack and a loop", () => {
  const d = dir("dest-b");
  run(["install", "--pack", "data-analytics", "--dest", d]);
  expect(exists(d, "dashboard-spec", "SKILL.md") && exists(d, "doc-critique", "SKILL.md"), "pack or its core skills missing");
  const l = dir("dest-c");
  run(["install", "--loop", "measure", "--dest", l]);
  expect(exists(l, "measure", "SKILL.md") && exists(l, "sql-review", "SKILL.md"), "loop or its stage skills missing");
});

check("project install into a git repo", () => {
  const repo = gitRepo("repo-project");
  run(["install", "doc-critique", "--project"], { cwd: repo });
  expect(exists(repo, ".claude", "skills", "doc-critique", "SKILL.md"), "--project did not write .claude/skills");
  run(["install", "md-to-xlsx", "--project", "--ide", "cursor"], { cwd: repo });
  expect(exists(repo, ".cursor", "skills", "md-to-xlsx", "SKILL.md"), "--ide cursor did not write .cursor/skills");
});

check("--local hides the install from git", () => {
  const repo = gitRepo("repo-local");
  run(["install", "output-hygiene", "--local"], { cwd: repo });
  expect(exists(repo, ".claude", "skills", "output-hygiene", "SKILL.md"), "--local did not copy the skill");
  const exclude = fs.readFileSync(path.join(repo, ".git", "info", "exclude"), "utf8");
  expect(exclude.includes("output-hygiene"), ".git/info/exclude does not list the skill");
  expect(git(repo, "status", "--porcelain").trim() === "", `git status is not clean:\n${git(repo, "status", "--porcelain")}`);
  run(["uninstall", "output-hygiene", "--local", "--yes"], { cwd: repo });
  expect(!exists(repo, ".claude", "skills", "output-hygiene"), "uninstall --local left the folder");
  expect(!fs.readFileSync(path.join(repo, ".git", "info", "exclude"), "utf8").includes("output-hygiene"), "exclude entry left behind");
});

check("install an agent", () => {
  const repo = gitRepo("repo-agent");
  run(["install", "--agent", "security-reviewer", "--project"], { cwd: repo });
  expect(exists(repo, ".claude", "agents", "security-reviewer.md"), "agent not written to .claude/agents");
});

check("--contain plans the sandbox from declared permissions", () => {
  const repo = gitRepo("repo-contain");
  const out = run(["install", "sonar-review", "--project", "--contain", "--dry-run"], { cwd: repo });
  expect(/allowedDomains: sonarcloud\.io(\s|$)/m.test(out) && out.includes("sandbox.enabled"), "containment plan missing the declared host");
  expect(!exists(repo, ".claude", "skills", "sonar-review"), "--dry-run wrote files");
});

check("a policy refuses a blocked skill and writes nothing", () => {
  const pol = path.join(TMP, "policy.json");
  fs.writeFileSync(pol, JSON.stringify({ version: 1, skills: { block: ["sql-review"] } }));
  const d = dir("dest-policy");
  const out = run(["install", "sql-review", "--dest", d, "--policy", pol], { ok: false });
  expect(/refused sql-review/.test(out), "refusal not reported");
  expect(!exists(d, "sql-review"), "a refused install wrote files");
});

check("loop-stats reads a log and writes the dashboard", () => {
  const log = path.join(TMP, "loop-log.jsonl");
  fs.writeFileSync(log, [
    { ts: "2026-10-01T10:00:00Z", loop: "build", stage: "verify", gate: "G2", verdict: "NOT READY", round: 1 },
    { ts: "2026-10-01T11:00:00Z", loop: "build", stage: "verify", gate: "G2", verdict: "READY", round: 2 },
  ].map((x) => JSON.stringify(x)).join("\n") + "\n");
  expect(json(["loop-stats", log, "--json"]).entries === 2, "loop-stats did not count two entries");
  const html = path.join(TMP, "stats.html");
  run(["loop-stats", log, "--html", html]);
  expect(fs.readFileSync(html, "utf8").includes("Content-Security-Policy"), "dashboard has no CSP");
});

check("a private catalogue: init, new-skill, validate", () => {
  const c = path.join(TMP, "team-catalogue");
  run(["init-catalogue", c, "--pack", "team"]);
  run(["new-skill", "release-checklist", "--pack", "team"], { cwd: c });
  expect(exists(c, "packs", "team", "skills", "release-checklist", "SKILL.md"), "new-skill did not scaffold the skill");
  run(["validate", "--from", c]);
});

check("package a mirror and verify it", () => {
  const m = path.join(TMP, "mirror");
  run(["package", m, "--pack", "core"]);
  expect(exists(m, "MIRROR.json"), "package wrote no MIRROR.json");
  run(["verify-mirror", m]);
  fs.appendFileSync(path.join(m, "packs", "core", "skills", "doc-critique", "SKILL.md"), "\ntampered\n");
  run(["verify-mirror", m], { ok: false });
});

check("inventory lists installs as JSON", () => {
  json(["inventory", "--json"], { cwd: TMP });
});

check("a skill's script runs with this OS's Python", () => {
  expect(PY, "no python3 or python on PATH");
  const src = path.join(ROOT, "packs", "converters", "skills", "md-to-xlsx");
  const out = path.join(TMP, "budget.xlsx");
  const md = path.join(TMP, "budget.md");
  fs.writeFileSync(md, "| Line | Amount | Due |\n|---|---:|---|\n| Hosting | 8,250.50 | 2026-11-15 |\n");
  execFileSync(PY, ["-I", path.join(src, "scripts", "md_to_xlsx.py"), md, "-o", out], { encoding: "utf8" });
  expect(fs.statSync(out).size > 1000, "no workbook written");
});

const only = process.argv[2];
let failed = 0;
for (const c of checks.filter((c) => !only || c.name.includes(only))) {
  const t = Date.now();
  try {
    c.fn();
    console.log(`ok    ${c.name}  (${Date.now() - t} ms)`);
  } catch (e) {
    failed++;
    console.log(`FAIL  ${c.name}\n      ${String(e.message).split("\n").join("\n      ")}`);
  }
}
try { fs.rmSync(TMP, { recursive: true, force: true }); } catch (e) { /* Windows can hold a handle briefly */ }
console.log(failed ? `\n${failed} check(s) failed on ${process.platform}.` : `\nAll checks passed on ${process.platform} (node ${process.version}).`);
process.exit(failed ? 1 : 0);

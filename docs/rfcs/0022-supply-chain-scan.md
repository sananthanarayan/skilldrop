---
rfc: 0022
title: Supply-chain scan for third-party catalogs
status: accepted   # draft → accepted | rejected → implemented
date: 2026-08-06
author: sananthanarayan
---

# RFC-0022: Supply-chain scan for third-party catalogs

## Problem / use case

skilldrop installs third-party content by design — any git URL or path via `--from` (RFC-0003), and
since RFC-0014 also agentbundle-shaped catalogs. Installs are copy-only and never execute, which is
genuinely safer than a manager that runs installers. But the residual risk isn't execution at
install time: **a `SKILL.md` is instructions an agent will obey**, and a bundled script is code that
runs on the user's machine later. The CLI warned about this in prose ("review each installed
SKILL.md before first use") — a warning with no evidence attached, which is easy to skim past.

Anthropic's own Agent Skills guidance makes the same point and prescribes the remedy: use skills
only from trusted sources, and *"audit thoroughly: review all files bundled in the Skill... look for
unusual patterns such as unexpected network calls, file access patterns, or operations that don't
match the Skill's stated purpose."* Every user is told to do a manual audit; nothing helped them do
it. A comparison against `luongnv89/asm` (which ships pre-install security scanning) confirmed this
is now table stakes for a skill installer.

## Fit check (structural change)

- **Reinforces the existing safety posture, doesn't replace it.** Copy-only install and the
  third-party warning are unchanged; the scan adds *evidence* to the warning.
- **Report, never block.** A match is a prompt to read a specific line, not a verdict. Blocking on a
  heuristic would fight the repo's "guided, not flooding" voice and would be wrong — a security
  skill legitimately discusses attacks, and a Figma client legitimately needs the network.
- **Zero dependencies.** Regex rules over files already on disk.
- **New command + flag** (`scan`, and `--json` on it) → a version bump per AGENTS.md.

## Proposal

Two rule sets, deliberately different, because prose and code carry different risks:

- **`SCRIPT_RULES`** over executable files (`.py`, `.js`, `.sh`, …): `exec-remote` (🟥 download-and-execute),
  `shell-exec` (🟧), `network` (🟧), `credentials` (🟧), `broad-fs` (🟨).
- **`PROSE_RULES`** over `SKILL.md`, matching only **instructions to misbehave** — `instruction-override`
  ("ignore previous instructions"), `conceal-from-user`, `memory-overwrite` ("update your MEMORY.md"),
  `prose-exfil` (send data to an external URL). Deliberately **not** security vocabulary, so a skill
  that is *about* injection (`threat-model`, `agent-threat-model`) is not flagged for discussing it.

Surfaces:
- **`skilldrop scan [<skill...>] [--from <src>] [--json]`** — audit a catalog without installing.
- **Automatic at install from a third-party catalog** — a compact digest printed after the existing
  warning, pointing at `skilldrop scan` for full detail. The bundled catalog is not auto-scanned.

Calibration was measured, not assumed: scanning skilldrop's own 51 skills yields **3 findings**, all
genuine and explainable (a `FIGMA_TOKEN` read; two `subprocess` calls in `gate.py`), with the
security-topic skills correctly unflagged.

**Known limitation, stated in the output:** a skill that *quotes* an attack pattern to teach
detection can match a prose rule — observed on agent-ready-repo's `assimilate-primitive`, which
quotes "update your SOUL.md / MEMORY.md" inside its own AST01 check. The tool says plainly that
matches are heuristics, not verdicts. Tuning to suppress quoted examples would trade false positives
for false negatives, which is the wrong direction for a security aid.

Anti-patterns this bans: blocking an install on a heuristic; implying a clean scan means a skill is
safe; scanning for security *vocabulary* rather than misbehaving *instructions*.

## Alternatives considered

- **Block the install on a 🟥 finding.** Rejected — false positives are inherent to the approach, and
  a blocked install teaches users to pass `--force`. Evidence plus a human decision is stronger.
- **Full AST/dataflow analysis.** Rejected — enormous cost, a dependency, and still not a proof.
  A first-pass reviewer's checklist is the honest scope.
- **Scan the bundled catalog automatically too.** Rejected — the bundled catalog is the repo's own,
  reviewed content; auto-scanning it every install would be noise. `skilldrop scan` covers it on demand.
- **Do nothing (copy-only is enough).** Rejected — copy-only addresses install-time execution, not
  the instruction-obedience and later-execution risks that Anthropic's own guidance highlights.

## Decision

Accepted and implemented in `bin/skilldrop.js`: a `scan` command (with `--json`) plus an automatic
compact scan on third-party installs. Calibrated against both skilldrop's own catalog and a real
third-party (agentbundle) catalog. skilldrop can now claim, accurately, *copy-only **and** scanned*.

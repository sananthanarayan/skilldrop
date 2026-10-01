---
title: skilldrop and the OWASP Top 10s
summary: Where skilldrop's controls meet the OWASP Agentic Skills Top 10 and the LLM Top 10 2025, what each control actually does, and the gaps it leaves.
kind: reference
---

# skilldrop and the OWASP Top 10s

skilldrop is a skill catalogue and an installer, not an LLM application. It has two kinds of
control, and the tables keep them apart:

- **Enforced:** code or CI that runs whether anyone reads a document or not. That means the
  installer (`bin/skilldrop.js`), the release and CI pipeline (`.github/`), and the guarantees
  in [SECURITY.md](../../SECURITY.md).
- **Advisory:** skills you run against *your own* agent or app, such as `agent-threat-model`,
  `agent-budget` and `llm-eval-harness`. They produce a design or a review, and enforce nothing
  at run time.

**Covered** means an enforced control or a dedicated skill addresses the risk's core
mitigations. **Partial** means the control is heuristic or advisory, or handles part of the
risk. **Not covered** means nothing in the repo addresses it.

Both lists are checked against OWASP's own sources: the [Agentic Skills Top 10](https://owasp.org/www-project-agentic-skills-top-10/)
v1.0-2026 (IDs and titles from the project's repository) and the
[LLM Top 10 2025](https://genai.owasp.org/llm-top-10/).

`skilldrop scan` tags each finding with the IDs it bears on, for example `[AST01, LLM01]`, and
`agent-threat-model` tags every 🟥 and 🟧 path the same way.

## OWASP Agentic Skills Top 10 (v1.0-2026)

| Risk | What skilldrop does | Coverage | Gap |
|---|---|---|---|
| **AST01 Malicious Skills** | `skilldrop scan` checks scripts for remote execution, shell, network, credential and broad filesystem patterns. It checks every markdown file in a skill (SKILL.md, reference, templates, examples) for instructions to override, conceal, rewrite memory, exfiltrate, or fetch remote instructions. It runs automatically after any `--from` install and `update`. Installs copy files and never execute them. | Partial | A heuristic that reports and never blocks, by design. Findings print after the files are copied. Agents are not scanned. |
| **AST02 Supply Chain Compromise** | `--from <git-url>#<commit>` pins a third-party catalog to an exact commit, which can't be moved the way a tag or branch can, and the CLI checks it got that commit. Every install records the commit in the ledger, and an unpinned install prints the pinned URL that reproduces it. skilldrop's own release has zero runtime dependencies, npm provenance through OIDC, SHA-pinned Actions, CODEOWNERS, Dependabot, CodeQL and gitleaks. | Partial | Third-party skills carry no signature, and pinning is opt-in. A catalogue owner who pushes a malicious commit still reaches anyone who installs unpinned. |
| **AST03 Over-Privileged Skills** | A skill that ships scripts declares `permissions`: the hosts it contacts, the programs it runs, and where it writes. `skilldrop scan` checks the scripts against it and raises any undeclared network call, command or broad write as a 🟥 finding, and `skilldrop validate` fails a catalogue that has one. All 24 bundled script skills declare theirs. Agents declare `tools:`, and projecting an agent to another IDE drops tools that have no equivalent, with a warning. | Partial | The check is only as good as the scan's patterns, so code that hides what it does can pass. Instruction-only skills (no scripts) declare nothing, though their prose can still tell an agent to run things. |
| **AST04 Insecure Metadata** | The structural gate refuses a whole install if any manifest is invalid JSON, a name doesn't match its folder, or a required field is missing. Frontmatter is read by pattern, never by a YAML loader. Skill names are regex-escaped before use. | Partial | Parsing is safe, but nothing checks meaning: an impersonating name or a misleading description passes. |
| **AST05 Untrusted External Instructions** | The scan's `remote-instructions` rule flags a skill that tells the agent to fetch instructions, rules or a prompt from a URL at run time. | Partial | A pattern match, so a paraphrase evades it. External material is not hash-pinned. |
| **AST06 Weak Isolation** | Only at install time: catalog content is never executed, and hooks are opt-in (`--with-hooks`) and printed. | Not covered | Installed skills run with the host agent's full permissions. skilldrop provides no sandbox. |
| **AST07 Update Drift** | The ledger keeps each skill's version, source, commit and a SHA-256 per file. `outdated` compares files as well as versions, so a skill changed upstream under the same version is named, and `update` takes it only with `--changed`. A pinned skill doesn't move until you re-pin it. `update` re-runs the structural gate and the supply-chain scan, keeps your edited files, and `update --dry-run` and `diff` show what would change first. | Covered | Detection needs the catalogue to be fetched; nothing watches it in the background. |
| **AST08 Poor Scanning** | The scan has a prose rule set aimed at natural-language instructions, kept separate from code rules and tuned not to flag skills that are *about* security. `--json` feeds other tools. | Partial | Pattern matching over prose is the weakness AST08 describes. RFC-0022 deliberately rejects semantic and LLM-assisted review. |
| **AST09 No Governance** | Each target has a ledger (an inventory), `doctor` checks it against disk, profiles give curated bundles, and `ai-usage-policy` writes an approved-tool list with owners. | Partial | Everything is per machine. There is no organisation-wide inventory, approval flow or audit log. |
| **AST10 Cross-Platform Reuse** | Installing across platforms is the product: Claude Code, Cursor, Kiro, Codex, Antigravity, Copilot and any folder. The `permissions` block travels inside `manifest.json` to every tool, and `skilldrop info` and third-party installs show it. Agent projection warns when a tool is dropped. | Partial | No target tool reads `permissions` itself; it informs the person installing, and the scan, but nothing enforces it at run time. |

**Covered 1 · Partial 8 · Not covered 1.**

## OWASP Top 10 for LLM Applications 2025

| Risk | What skilldrop does | Coverage | Gap |
|---|---|---|---|
| **LLM01:2025 Prompt Injection** | The scan's prose rules flag injection-shaped instructions in a skill's own files. Advisory: `agent-threat-model` builds the lethal-trifecta matrix, keeps a bank of injection vectors, and holds that a system prompt is not a boundary. | Partial | No run-time defence. SECURITY.md puts injection against your agents out of scope. |
| **LLM02:2025 Sensitive Information Disclosure** | The scan's credential and exfiltration rules. The `security-reviewer` agent checks diffs for secrets and needless PII. `agent-threat-model` sweeps egress, including rendered markdown. `ai-usage-policy` sets data tiers. | Partial | Detection and advice; nothing redacts. |
| **LLM03:2025 Supply Chain** | skilldrop's own distribution, listed under AST02. Third-party catalogs get the structural gate, a review warning and the scan. | Partial | Nothing covers model, dataset or adapter provenance, which is the core of LLM03. |
| **LLM04:2025 Data and Model Poisoning** | `agent-threat-model` names poisoned retrieval documents as an injection vector. | Not covered | No guidance on training or embedding data provenance. |
| **LLM05:2025 Improper Output Handling** | `security-reviewer` traces source to sink in diffs. `agent-threat-model` names rendered egress. | Partial | No skill specific to treating model output as untrusted input to SQL, shell or HTML. |
| **LLM06:2025 Excessive Agency** | `agent-threat-model` inventories capability, transitive reach and inherited capability, and checks that human gates show the real payload. `agent-budget` sets caps. The installer never executes content and makes hooks opt-in. | Covered | Advisory: nothing enforces least privilege at run time. |
| **LLM07:2025 System Prompt Leakage** | `agent-threat-model` refuses the system prompt as a security boundary and tags paths that rely on one. | Partial | No leakage testing. |
| **LLM08:2025 Vector and Embedding Weaknesses** | `agent-threat-model` tags writable retrieval sources. | Not covered | No skill on access control or tenant isolation in vector stores. |
| **LLM09:2025 Misinformation** | `llm-eval-harness` builds golden sets with adversarial cases and a validated judge for faithfulness. `ai-usage-policy` sets human review by consequence. | Partial | No grounding or citation check at run time. |
| **LLM10:2025 Unbounded Consumption** | `agent-budget` sets per-stage token caps that abort rather than warn, under a run-level cap. | Partial | Covers agent loops only, not public endpoints or rate limits. |

**Covered 1 · Partial 7 · Not covered 2.**

## The biggest gaps, in order

1. **No run-time isolation** (AST06). Installed skills run with the host agent's full
   permissions. That belongs to the agent host, not an installer, but a skill could at least
   say what containment it expects.
2. **The scan is pattern matching** (AST08). That's a deliberate trade for a zero-dependency,
   offline CLI, and it limits how much the `permissions` check can prove. The weekly evals and
   human review are the backstop.
3. **No signing for third-party catalogues** (AST02). Commit pins stop a moved tag; they don't
   prove who wrote the commit.
4. **No organisation-wide governance** (AST09): inventory, approval and audit stay per machine.
   `skilldrop package` mirrors and `MIRROR.json` are the closest thing today.

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
| **AST02 Supply Chain Compromise** | `--from <git-url>#<tag>` pins a third-party catalog, and the ledger records each skill's source. skilldrop's own release has zero runtime dependencies, npm provenance through OIDC, SHA-pinned Actions, CODEOWNERS, Dependabot, CodeQL and gitleaks. | Partial | Third-party skills carry no signature. Pinning is optional and uses a tag or branch, which can move, and the ledger records no commit SHA. |
| **AST03 Over-Privileged Skills** | Agents declare `tools:`, and projecting an agent to another IDE drops tools that have no equivalent, with a warning. Manifests declare `deps` and `env`. The scan's network, shell and credential rules stand in for undeclared capability. | Partial | Skills have no permission manifest, so declared and observed capability can't be compared. |
| **AST04 Insecure Metadata** | The structural gate refuses a whole install if any manifest is invalid JSON, a name doesn't match its folder, or a required field is missing. Frontmatter is read by pattern, never by a YAML loader. Skill names are regex-escaped before use. | Partial | Parsing is safe, but nothing checks meaning: an impersonating name or a misleading description passes. |
| **AST05 Untrusted External Instructions** | The scan's `remote-instructions` rule flags a skill that tells the agent to fetch instructions, rules or a prompt from a URL at run time. | Partial | A pattern match, so a paraphrase evades it. External material is not hash-pinned. |
| **AST06 Weak Isolation** | Only at install time: catalog content is never executed, and hooks are opt-in (`--with-hooks`) and printed. | Not covered | Installed skills run with the host agent's full permissions. skilldrop provides no sandbox. |
| **AST07 Update Drift** | The ledger keeps each skill's version, source and a SHA-256 per file. `outdated` shows what changed. `update` is explicit, re-runs the structural gate and the supply-chain scan, and keeps your edited files, writing new versions as `.upstream`. `update --dry-run` and `diff` show what would change first. | Partial | Updates are triggered by the version string, so content that changes without a version bump goes unnoticed. |
| **AST08 Poor Scanning** | The scan has a prose rule set aimed at natural-language instructions, kept separate from code rules and tuned not to flag skills that are *about* security. `--json` feeds other tools. | Partial | Pattern matching over prose is the weakness AST08 describes. RFC-0022 deliberately rejects semantic and LLM-assisted review. |
| **AST09 No Governance** | Each target has a ledger (an inventory), `doctor` checks it against disk, profiles give curated bundles, and `ai-usage-policy` writes an approved-tool list with owners. | Partial | Everything is per machine. There is no organisation-wide inventory, approval flow or audit log. |
| **AST10 Cross-Platform Reuse** | Installing across platforms is the product: Claude Code, Cursor, Kiro, Codex, Antigravity, Copilot and any folder. Agent projection warns when a tool is dropped. | Partial | Skills carry no security metadata, so there is nothing to keep when a skill moves between tools. |

**Covered 0 · Partial 9 · Not covered 1.**

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

1. **No signing or commit pinning for third-party catalogs** (AST02, AST07). Recording the
   resolved commit SHA in the ledger, and warning when `update` sees new content under an
   unchanged version, would close most of it.
2. **No permission manifest for skills** (AST03, AST10). Declaring network, shell and
   filesystem needs would give the scan something to compare against and a property to carry
   across tools.
3. **The scan is pattern matching** (AST08). That's a deliberate trade for a zero-dependency,
   offline CLI. The weekly evals and human review are the backstop.
4. **No run-time isolation** (AST06). That belongs to the agent host, not an installer, but a
   skill could at least say what containment it expects.

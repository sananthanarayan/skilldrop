# skill-review reference

The checklist behind each review area, the safety categories, and the verdict rules. Items
marked **(lint)** are checked by `scripts/lint_skill.py`. The rest need you.

## 1. Description and routing

A router sees the frontmatter `name` and `description` of every installed skill and picks
one. It does not read the body first.

| Check | Fails when | Severity |
|---|---|---|
| Present and in range **(lint)** | No description, or over 1,024 characters (the Agent Skills specification limit) | 🟥 |
| Name format **(lint)** | Not lowercase letters, digits and single hyphens, over 64 characters, or not equal to the folder name | 🟥 |
| Leads with the artifact | Opens with "This skill…", "Helps…", or a technique name instead of what it produces | 🟧 |
| Ends with triggers **(lint, partly)** | No "Use when…" clause, or triggers that are abstract ("for productivity") rather than phrases a user types | 🟧 |
| Long enough to discriminate **(lint)** | Under ~120 characters: rarely names both the artifact and the moment to use it | 🟨 |
| No sibling collision **(lint, partly)** | Another installed skill's description claims the same requests, and neither says when not to use it | 🟧 |
| Not over-broad | Claims every request in a domain ("anything to do with docs") so it wins queries it can't serve | 🟧 |

The lint's `--siblings` overlap score is the share of content words two descriptions have in
common. Across skilldrop's own catalogue the closest pair of distinct skills scores 0.16, so
the script warns at 0.20. A low score does not prove there's no collision: two descriptions
can share few words and still claim the same request. Test it by reading each sibling's
should-trigger queries against this skill's description.

**How to write the fix.** Give the rewritten description in full, and for each collision a
when-not line naming the sibling and a should-not-trigger query that belongs to it.

## 2. Portability

The same folder is read by Claude Code (`.claude/skills/`), Codex and Antigravity
(`.agents/skills/`), Copilot (`.github/skills/`, and `.claude/skills/` in Copilot CLI), Kiro
(`.kiro/skills/`), and by Cursor, Continue, Cline and Aider through a rule or an attached file.

| Check | Fails when | Severity |
|---|---|---|
| Script paths have a fallback **(lint)** | `${CLAUDE_SKILL_DIR}/x` appears with no plain relative `x`. Only Claude Code sets that variable | 🟧 (🟥 if the skill is useless without the script) |
| No absolute paths **(lint)** | `/Users/<name>/`, `/home/<name>/`, or a Windows user-profile path in instructions or templates | 🟧 |
| Paths resolve **(lint)** | A link or in-skill path names a file that doesn't exist | 🟥 |
| No silent tool-specific syntax | Slash commands, MCP tool names, hooks or `allowed-tools` grants presented as universal, with no line on what other tools should do | 🟨 |
| Dependencies declared | A script imports a third-party package, or needs a binary, and SKILL.md never says so | 🟧 |
| Output path chosen by the user | A script writes to a fixed location, or into the skill folder | 🟨 |
| Python and shell portable | Python syntax newer than the stated minimum, or bash-only constructs in a script described as POSIX | 🟨 |

## 3. Safety

A skill is instruction text an agent obeys, plus code that runs on the user's machine. The lint
runs the same pattern families as `skilldrop scan` (RFC-0022). These are heuristics: a
skill that *discusses* an attack is not performing it, so read every hit.

**Prose rules** (every `.md` file in the folder):

| Rule id | What the line makes the agent do | Lint level | OWASP |
|---|---|---|---|
| `instruction-override` | Discard the instructions it was given earlier | ERROR | AST01, LLM01 |
| `conceal-from-user` | Keep an action or a result from the user | ERROR | AST01, LLM01 |
| `memory-overwrite` | Rewrite its own memory or policy file (MEMORY.md, CLAUDE.md, AGENTS.md) | ERROR | AST01, LLM01 |
| `prose-exfil` | Send or upload data to an external address | WARN | AST01, LLM02 |
| `remote-instructions` | Obtain its rules or prompt from a web address at run time, so what it obeys can change after review | WARN | AST05, LLM01 |

**Script rules** (`.py`, `.js`, `.sh` and other executables):

| Rule id | What the code does | Lint level | OWASP |
|---|---|---|---|
| `exec-remote` | Downloads content and pipes it into a shell or an eval | ERROR | AST01, AST02 |
| `shell-exec` | Runs shell commands | WARN | AST03, LLM06 |
| `network` | Makes outbound network calls | WARN | AST03, LLM02 |
| `credentials` | Reads tokens, keys, `.ssh`/`.aws` files or dotenv files | WARN | AST01, LLM02 |
| `broad-fs` | Deletes recursively or writes to system folders | INFO | AST03, LLM06 |

**What the patterns miss, and you check:**

- Paraphrases of the prose rules: "quietly", "in the background", "no need to mention",
  "grab the current guidelines from our wiki URL before each run".
- Broad shell grants: "run any command needed", a hook that runs on every session, an
  `allowed-tools` entry that allows all of Bash.
- Destructive steps with no confirmation: deleting files, force-pushing, dropping tables.
- A mismatch between purpose and capability: a formatting skill whose script opens a socket,
  or reads environment variables it never uses for its stated job.
- Secrets or real customer data in templates and examples.

**OWASP Agentic Skills Top 10 (v1.0-2026)**, the IDs to tag findings with:

| ID | Risk | What to look for in one skill folder |
|---|---|---|
| AST01 | Malicious Skills | Instructions or code that work against the user: hidden actions, credential reads, data leaving the machine |
| AST02 | Supply Chain Compromise | Scripts that pull and run remote code, unpinned downloads at run time |
| AST03 | Over-Privileged Skills | Shell, network or file access beyond what the stated job needs |
| AST04 | Insecure Metadata | A name or description that impersonates another skill or misstates what it does |
| AST05 | Untrusted External Instructions | Rules, prompts or skill text loaded from a URL at run time |
| AST06 | Weak Isolation | Steps that assume no sandbox and touch the wider system without saying so |
| AST07 | Update Drift | Behaviour that depends on remote content that can change without a version change |
| AST08 | Poor Scanning | Not a finding about the skill. Note when you relied on patterns alone |
| AST09 | No Governance | No owner, version or source recorded, for a skill meant to be shared |
| AST10 | Cross-Platform Reuse | Security assumptions that hold in one tool and not another, such as a permission prompt only Claude Code shows |

Severity for safety: a confirmed instruction to act against the user, or remote code
execution, is 🟥 and forces `FIX FIRST` at least. A capability the job needs but SKILL.md
doesn't declare (a script that shells out to Chrome to make a PDF) is 🟨 with the fix
"say so in SKILL.md".

## 4. Structure

| Check | Fails when | Severity |
|---|---|---|
| Length **(lint)** | SKILL.md over ~500 lines | 🟨 |
| Steps decide | Steps say "consider", "you might", "depending on preference" instead of picking a default | 🟧 |
| Quality bar **(lint)** | No checkable definition of a good output | 🟧 |
| When / when-not **(lint, partly)** | No boundary, or when-not lines that don't name the alternative | 🟧 |
| Anti-patterns **(lint)** | None, or generic ones ("don't be vague") instead of real failure modes | 🟨 |
| Non-interactive rule **(lint, partly)** | The skill asks questions but says nothing about subagent or CI runs, where nobody can answer | 🟨 |
| No orphans **(lint)** | A reference file or script that SKILL.md never mentions, so no agent reads or runs it | 🟨 |
| Questions capped | More than two rounds of clarifying questions before any output | 🟨 |

## 5. Eval coverage

| Check | Fails when | Severity |
|---|---|---|
| Acceptance evals exist **(lint)** | No `evals/evals.json`, or an eval with no assertions | 🟧 |
| Assertions are checkable | Assertions like "output is high quality" that nobody can mark pass or fail | 🟧 |
| Assertions trace to the quality bar | Quality bar items with no matching assertion | 🟨 |
| No-invention assertion | A skill that handles user facts has no "does not invent X" assertion | 🟧 |
| Trigger queries **(lint)** | Fewer than 4 should-trigger or 3 should-not-trigger queries | 🟨 |
| Near-misses are real | Should-not-trigger rows nobody would type, or rows that don't name a sibling | 🟨 |

## Verdict rules

| Verdict | When |
|---|---|
| `READY` | No 🟥, at most two 🟧, and no safety finding above 🟨 |
| `FIX FIRST` | Any 🟥 or 🟧 safety finding that local edits fix, or three or more 🟧 |
| `REWRITE` | No single clear artifact, a description that can't be fixed without changing what the skill does, or more than half of SKILL.md would change |

`REWRITE` beats `FIX FIRST` when both apply.

---
name: skill-review
description: Audit an existing Agent Skill folder (SKILL.md plus its scripts, references and evals) for Claude Code, Codex, Copilot, Cursor, Kiro or Antigravity, and return a READY / FIX FIRST / REWRITE verdict with severity-tagged findings across five areas — whether a router would pick it and whether it collides with a sibling, portability, safety (mapped to the OWASP Agentic Skills Top 10), structure, and eval coverage — backed by a stdlib lint script for the mechanical checks. Use when the user says "review this skill", "is my SKILL.md any good", "why doesn't my skill trigger", "is this skill safe to install", or wants a skill checked before sharing or publishing it.
---

# skill-review

You audit one skill folder the way a router, a second tool and a suspicious installer would
see it. A skill fails in five places: the description doesn't win the routing decision, it
works only in the tool it was written in, it tells the agent to do something unsafe, its
structure leaves the agent guessing, or nothing tests it. The lint script settles the
mechanical half. Your job is the half a regex can't see. The counterpart that writes a skill
from scratch is `skill-author`.

## How to respond

1. **Get the folder, ask once for what's missing.** You need the skill folder (a path, or the
   pasted files) and, if the user has them, the sibling skills it will sit next to. Ask both in
   one message. Without siblings, the collision check covers only what the user named.

2. **Run the lint first.** It checks frontmatter, the name against the folder, description
   length and trigger phrases, that every path the SKILL.md names exists, `CLAUDE_SKILL_DIR`
   paths with no plain fallback, absolute paths, line count, unlinked reference files, eval
   shape, and the `skilldrop scan` safety patterns:

   ```bash
   # Claude Code
   python3 "${CLAUDE_SKILL_DIR}/scripts/lint_skill.py" path/to/my-skill --siblings path/to/skills
   # Other IDEs (from the skill folder)
   python3 scripts/lint_skill.py path/to/my-skill --siblings path/to/skills
   ```

   Exit 1 means at least one ERROR. Add `--json` for machine output and `-o report.txt` to
   save it. If Python isn't available, walk the same checks by hand from
   [`reference.md`](reference.md) and say so in the report. Paste the lint result into the
   report as-is. Don't retype or tidy it.

3. **Read the whole folder before judging.** SKILL.md, every reference file, every script, the
   evals. A safety instruction can sit in an example. A script can do more than SKILL.md says
   it does.

4. **Judge the description as a router would.** Read the frontmatter description alone, then
   ask three questions. Does it lead with the artifact? ✅ *"Write a release-notes page from
   merged pull requests…"* ❌ *"A helpful skill for releases."* Does it end with phrases a user
   would actually type? Would it beat each named sibling for that sibling's own queries, or
   lose to them for its own? For every sibling with real overlap, name the query that would
   go to the wrong skill and the words to add to the description or the when-not section.

5. **Check portability.** Look for Claude-only variables with no fallback, absolute or
   home-directory paths, tool-specific syntax used as if it were universal (a slash command,
   an MCP tool name, `allowed-tools` grants, a hook), scripts that need a package nobody
   declared, and scripts that write to a fixed location. The same folder should work when
   copied into `.agents/skills/`, `.github/skills/` or `.kiro/skills/`.

6. **Check safety against the categories in [`reference.md`](reference.md).** Treat each lint
   safety hit as a lead, not a verdict: read the line and decide. Then look for what the
   patterns miss: paraphrased instructions to fetch remote content, to act quietly, to edit
   the agent's own memory or policy files, broad shell ("run whatever is needed"), destructive
   commands with no confirmation, and a script whose behaviour doesn't match the stated
   purpose. Tag each finding with its OWASP Agentic Skills ID (AST01–AST10) from the mapping in
   the reference.

7. **Check structure.** Does SKILL.md have numbered steps, a quality bar, when and when-not
   sections with named alternatives, anti-patterns, and a non-interactive rule? Is it under
   about 500 lines, with long material split out and linked? Are there orphan files, or steps
   that say "consider" where they should decide?

8. **Check eval coverage.** Do the acceptance assertions restate the quality bar as checkable
   claims about one output? Does a fact-handling skill have a "does not invent X" assertion?
   Do the should-not-trigger queries name real siblings, and would anyone actually type them?

9. **Rate every finding and pick the verdict.** Severity: 🟥 blocker (it won't load, won't
   route, or is unsafe to install), 🟧 major (it works but fails a promise or a second tool),
   🟨 minor, ⚪ nit. When unsure between two, pick the lower one. The verdict is mechanical:
   - `READY`: no blockers, at most two majors, and no safety finding above 🟨.
   - `FIX FIRST`: any blocker or 🟧 safety finding that a local edit fixes, or three or more majors.
   - `REWRITE`: the skill has no clear single artifact, the description can't be fixed without
     changing what the skill does, or more than half of SKILL.md would change.

10. **Write the report** with [`templates/review.md`](templates/review.md): the verdict line
    and a three-sentence summary first, the lint output, findings grouped by area, each with
    **Where** (file:line or a short quote), **What** (one sentence), and **Fix** (the
    replacement text where it fits in a line or two), then "What's working". For `REWRITE`,
    say what the one artifact should be and point to `skill-author`.

**Non-interactive runs** (subagent, CI, headless): with no folder path or pasted SKILL.md,
emit `BLOCKED: need the skill folder (path or SKILL.md contents)` and stop. Missing siblings
degrade to an `[assumption]` line at the top stating that collisions were checked only
against the skills named in the folder itself.

## Useful references in this skill

- [`reference.md`](reference.md) — the full checklist per area, the safety categories mapped to `skilldrop scan` rule ids and OWASP AST IDs, and the verdict rules
- [`templates/review.md`](templates/review.md) — the report skeleton
- [`scripts/lint_skill.py`](scripts/lint_skill.py) — the mechanical lint (stdlib, Python 3.9+, no network)
- [`examples/meeting-notes-review.md`](examples/meeting-notes-review.md) — a deliberately broken skill, the real lint output, and the review written from it

## Quality bar

- **The verdict follows the rules in step 9**, and the counts in the verdict line match the findings below it.
- **Lint output is pasted verbatim**, and every lint ERROR either appears as a finding or is explained away in one line.
- **Every finding has a location and a concrete fix.** "Improve the description" is not a fix. The rewritten sentence is.
- **Collision findings name the sibling and the query** that would route wrongly.
- **Safety findings carry an AST ID** and say what the line makes the agent do, not just which pattern matched.
- **Judgment goes beyond the lint.** At least one finding, or an explicit "nothing beyond the lint", covers what the regexes can't see: routing, paraphrased safety issues, steps that don't decide.
- **It reviews the skill, not the task.** Whether release notes should exist is out of scope. Whether this skill writes them reliably is the job.

## When to use this skill

- ✅ Before sharing a skill with a team or publishing it to a marketplace or catalogue
- ✅ A skill that doesn't trigger, or triggers for the wrong requests
- ✅ Deciding whether a third-party skill is safe to install
- ✅ Checking a skill written for Claude Code still works in Codex, Copilot, Cursor or Kiro

## When NOT to use this skill

- ❌ Writing a new skill from a task description: use `skill-author`
- ❌ Adding a skill to the skilldrop catalogue itself, which has its own manifest and `validate.py` rules: use `contribution-wizard`
- ❌ Generating more eval cases for a skill whose only gap is coverage: use `eval-harness-generator`
- ❌ Reviewing a repo's always-on AGENTS.md policy file: use `agents-md-generator`
- ❌ Threat-modelling the agent deployment that runs skills (its tools, data and egress): use `agent-threat-model`
- ❌ Critiquing an ordinary document such as an ADR or design doc: use `doc-critique`

## Anti-patterns to avoid

- ❌ **Lint-only reviews.** A clean lint with a description that loses every routing decision is still `FIX FIRST`.
- ❌ **Treating every pattern hit as malicious.** A threat-model skill that *describes* prompt injection is not injecting. Read the line.
- ❌ **Severity inflation.** A missing nit-level heading is not a blocker. If blockers outnumber majors, recheck.
- ❌ **"Make the description clearer."** Write the new description.
- ❌ **Running the skill's scripts to see what they do.** Read them. A review never executes untrusted code.
- ❌ **Reviewing against one tool's quirks.** A Claude-Code-only frontmatter field is a portability note, not a blocker, unless the skill claims to be portable.

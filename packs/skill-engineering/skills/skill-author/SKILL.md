---
name: skill-author
description: Write a new portable Agent Skill (a SKILL.md folder) from a described task, for Claude Code, Codex, Copilot, Cursor, Kiro or Antigravity in any repo — a description that leads with the artifact and ends with trigger phrases, decisive steps, a quality bar, when and when-not sections naming near-miss siblings, anti-patterns, a non-interactive rule, reference files and scripts that work in every tool, acceptance evals and trigger queries, and the install path for each tool. Use when the user says "turn this into a skill", "write a SKILL.md for…", "make an agent skill that…", or wants a repeatable task packaged so their coding agent does it the same way every time.
---

# skill-author

You write one skill folder that does one task well and loads in every tool that reads
SKILL.md. Most skills fail before the body is read: the description is vague, so the router
never picks it, or it overlaps a sibling and wins the wrong requests. So you spend the
interview on three things, the deliverable, the trigger phrases and the near-miss siblings,
and decide everything else yourself. Once it's written, `skill-review` audits it.

## How to respond

1. **Interview once, in one message.** Take what the user already said and ask only for the
   gaps. Suggest defaults so they can answer "go".

   > 1. **The deliverable:** what file or output does the skill produce, and what makes one good?
   > 2. **The triggers:** three to five things you'd actually type to ask for it.
   > 3. **The near-misses:** which nearby requests should *not* use it, and which skill or tool
   >    handles them instead? List any skills already installed next to it.
   > 4. **The inputs:** what does the agent get (a paste, a file, a repo), and which facts must it
   >    never make up?
   > 5. **Tools and repo:** which tools, and where it lives. *Default: every tool, project scope.*

   If the user describes a task with no single artifact ("help with our backend"), stop and
   ask what the one output is. A skill with no artifact can't have a quality bar.

2. **Check that it should be a skill.** A skill is a repeatable task with one artifact that
   the agent loads on demand. An always-on rule for the whole repo ("use pnpm", "never edit
   generated files") belongs in AGENTS.md, so point the user to `agents-md-generator`. A
   one-off task needs a prompt, not a skill. Say which, and stop if it isn't a skill.

3. **Name it.** Kebab-case, artifact first, at most 64 characters, identical to the folder
   name. ✅ `release-notes-from-prs` ❌ `ReleaseHelper`, `release-notes-v2`, `my-skill`.

4. **Write the description, then test it against the siblings.** Formula: artifact and use
   case, then two or three distinguishing details, then `Use when the user …, says "…", "…".`
   Stay under 1,024 characters (the Agent Skills specification limit); 250–600 is the useful
   range.
   - ✅ *"Write customer-facing release notes from merged pull requests — grouped New / Improved /
     Fixed, internal changes dropped, breaking changes first. Use when the user pastes merged
     PRs and says "write the release notes" or "draft the changelog"."*
   - ❌ *"A helpful skill for release management and documentation tasks."*

   For each near-miss sibling, read your description as if you were routing that sibling's
   request. If yours would win it, add the distinguishing words now. Rules for wording are in
   [`reference.md`](reference.md).

5. **Write SKILL.md from [`templates/skill-template.md`](templates/skill-template.md)**, sections
   in this order: title and a short intro naming the siblings, `How to respond` (numbered,
   imperative, with asking once for missing inputs as step 1), the non-interactive line,
   useful references, `Quality bar`, `When to use`, `When NOT to use` (each line naming the
   alternative), `Anti-patterns to avoid`. Steps decide: pick defaults, cap questions at two,
   and show a ✅ and a ❌ example wherever a rule could be read two ways.

6. **Write the non-interactive rule.** One self-contained line: in a subagent, CI or headless
   run, which missing inputs become an `[assumption]` line at the top of the output, and which
   stop the run with `BLOCKED: need <X>`. Block on anything whose invention would corrupt the
   artifact: the user's facts, numbers, names, dates.

7. **Split long material out.** Keep SKILL.md under about 500 lines; 100–250 is typical. Move
   lookup tables, long rubrics and worked examples into `reference.md` or a `references/`
   folder, and link every file from SKILL.md with a relative link. An unlinked file is never
   read.

8. **Add a script only for work that must be exact:** arithmetic, parsing, file conversion,
   validation. Use the standard library, read input from arguments or stdin, write to a path
   the user gives, and exit non-zero with a clear message on bad input. Reference it both
   ways, because only Claude Code sets `CLAUDE_SKILL_DIR`:

```bash
# Claude Code
python3 "${CLAUDE_SKILL_DIR}/scripts/<script>.py" <args>
# Other tools (run from the skill folder)
python3 scripts/<script>.py <args>
```

   Run the script on a real input and on a bad one before shipping it. Any example output in
   the skill must be pasted from a real run.

9. **Write the evals.** `evals/evals.json` holds one or two realistic prompts with concrete
   details and placeholder names (Acme, Northwind), each with five to eight assertions taken
   from the quality bar. A skill that handles facts gets a "does not invent X" assertion.
   `evals/eval_queries.json` holds at least four should-trigger phrasings and three or four
   should-not-trigger near-misses, each one belonging to a sibling named in When NOT to use.
   Shapes are in [`templates/evals.json`](templates/evals.json) and
   [`templates/eval_queries.json`](templates/eval_queries.json).

10. **Hand over the folder and the install line.** Show the file tree, then every file in full,
    then where to put it for each of the user's tools (the table in [`reference.md`](reference.md)).
    Close with the check: run `skill-review` on the folder, or its lint script, then one eval
    prompt in a fresh session.

**Non-interactive runs** (subagent, CI, headless): with no deliverable named, emit
`BLOCKED: need the skill's deliverable (what file or output it produces)` and write nothing.
Missing triggers, siblings or tools degrade to `[assumption]` lines at the top: triggers
derived from the task wording, no siblings checked, every tool targeted.

## Useful references in this skill

- [`reference.md`](reference.md) — description rules with passing and failing examples, the frontmatter fields, per-tool install paths, portability rules, the script contract, and the eval formats
- [`templates/skill-template.md`](templates/skill-template.md) — the SKILL.md skeleton, sections in order
- [`templates/evals.json`](templates/evals.json) and [`templates/eval_queries.json`](templates/eval_queries.json) — eval shapes
- [`examples/release-notes-skill.md`](examples/release-notes-skill.md) — a described task, the interview, and the finished folder with its real lint output

## Quality bar

- **The description leads with the artifact and ends with trigger phrases** a user would actually type, and is under 1,024 characters.
- **Name equals folder name**, kebab-case, at most 64 characters.
- **Every near-miss sibling the user named appears twice:** in a When NOT line and in a should-not-trigger query.
- **Steps decide.** No "consider", "you might", or "depending on preference"; at most two clarifying questions.
- **A quality bar and anti-patterns are present**, and the evals' assertions restate the quality bar as checkable claims.
- **Portable:** every script appears in both the `${CLAUDE_SKILL_DIR}` form and the plain relative form; no absolute paths; no tool-only syntax without saying what other tools do.
- **Nothing is invented.** Install paths come from the reference table, and example outputs come from real runs.

## When to use this skill

- ✅ Packaging a task the user repeats (a report, a review, a conversion) as a skill for their coding agent
- ✅ Turning a long prompt the user keeps pasting into a SKILL.md folder
- ✅ Writing a skill for a team repo that people use from different tools

## When NOT to use this skill

- ❌ Adding a skill to the skilldrop catalogue itself, with its manifest, pack and `validate.py` rules: use `contribution-wizard`
- ❌ Auditing a skill that already exists: use `skill-review`
- ❌ Adding evals to an existing skill without changing it: use `eval-harness-generator`
- ❌ Repo-wide always-on rules for agents (commands, conventions, forbidden actions): use `agents-md-generator`

## Anti-patterns to avoid

- ❌ **The "helpful assistant" description.** "Helps with documentation tasks" matches everything and wins nothing. Name the artifact.
- ❌ **Triggers nobody types.** "Use for knowledge management workflows." Write what the user says: "write up the meeting notes".
- ❌ **A skill that does five things.** Five artifacts mean five quality bars. Split it.
- ❌ **Claude-only script paths.** A script reached only through the `CLAUDE_SKILL_DIR` variable, with no plain relative path beside it, breaks in every other tool.
- ❌ **Asking eight questions before writing anything.** Ask for the deliverable, the triggers and the siblings; default the rest.
- ❌ **Near-miss queries invented to fill the file.** Each should-not-trigger row belongs to a real sibling the user has.
- ❌ **A skill that calls another skill.** Skills install one at a time, so a skill that needs a sibling breaks when copied alone. Name the sibling as a next step instead.

---
name: {artifact-first-kebab-name, same as the folder}
description: {Verb + the artifact} {for what use case} — {two or three details that set it apart from its siblings}. Use when the user {situation}, says "{phrase they type}", "{phrase}", or "{phrase}".
---

# {name}

{Two or three sentences: what the skill produces, for whom, and how it differs from the
nearest sibling ("for X, use {sibling} instead").}

## How to respond

1. **Ask once for what's missing.** {The inputs the skill needs, asked in one message, with a
   default shown for each so the user can reply "go". At most two real questions.}
2. **{Imperative verb.}** {The instruction, with the default it picks.}
   ✅ *"{a passing example}"* ❌ *"{a failing example}"*
3. **{Imperative verb.}** {…}
4. **Run the script** (only if the skill has one):

   ```bash
   # Claude Code
   python3 "${CLAUDE_SKILL_DIR}/scripts/{script}.py" {args}
   # Other tools (run from the skill folder)
   python3 scripts/{script}.py {args}
   ```

5. **Emit with {the template file}** in one message.

**Non-interactive runs** (subagent, CI, headless): {inputs that become an `[assumption]` line
at the top of the output}. With no {the anchor input whose invention would corrupt the
artifact}, emit `BLOCKED: need {X}` and write nothing.

## Useful references in this skill

- [{reference file}]({relative path}) — {one line on what it holds}

## Quality bar

- **{Checkable rule about the output.}** {Why, in one short sentence.}
- **{The output does not invent X that the input did not give.}**

## When to use this skill

- ✅ {A situation a user is actually in}

## When NOT to use this skill

- ❌ {A near-miss request}: use {the sibling skill or tool that handles it}

## Anti-patterns to avoid

- ❌ **{A real mistake, named.}** {What it looks like and why it fails.}

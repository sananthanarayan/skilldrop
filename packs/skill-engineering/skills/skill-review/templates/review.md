# Skill review: {skill-name}
_Folder: {path} · Reviewed: {YYYY-MM-DD} · Siblings checked: {list, or "none given [assumption]"}_

## Verdict
**{READY | FIX FIRST | REWRITE}** — {N} blocker, {N} major, {N} minor, {N} nit

{Three sentences: what the skill is for, the finding that decides the verdict, and what to do first.}

## Lint output

```
{paste lint_skill.py output verbatim}
```

## Findings

### Description and routing
1. 🟧 **Where:** {SKILL.md frontmatter, or "quote"}
   **What:** {one sentence}
   **Fix:** {replacement text}

### Portability
…

### Safety
1. 🟥 **Where:** {file:line}  [{AST0N}]
   **What:** {what the line makes the agent or script do}
   **Fix:** {the edit}

### Structure
…

### Eval coverage
…

## Suggested description

```
{the full rewritten description, only when routing findings call for one}
```

## What's working
- {2-4 specific strengths worth keeping in a rewrite}

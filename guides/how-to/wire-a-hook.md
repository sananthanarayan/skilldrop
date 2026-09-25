---
title: Wire a skill to an event
summary: Opt-in hooks: how a loop-shaped skill binds to session-start or pre-commit-review, and how the CLI projects that onto each target.
kind: how-to
---

# Wire a skill to an event

#### Hooks (opt-in) — wire a skill to an event

Some loop-shaped skills declare **hooks** — event-triggered nudges the CLI wires into your environment when you pass `--with-hooks` ([RFC-0006](../../docs/rfcs/0006-per-ide-hooks.md)). It's off by default, so a plain install never touches your git repo or editor settings.

```bash
npx skilldrop-cli install devils-advocate --with-hooks --project
# → appends a marker-fenced reminder to .git/hooks/pre-commit: "run /devils-advocate on staged changes"
```

The CLI emits per target and **degrades gracefully** — a `pre-commit-review` hook becomes an IDE-agnostic git hook (needs a git repo); a `session-start` hook becomes a Claude Code `settings.json` entry, and is cleanly skipped where the target has no equivalent (Cursor, Kiro, plain `--dest`), printing what it did and where. Kiro, Codex, and Copilot all have native hook mechanisms the CLI does not emit into yet — see [`docs/designs/ide-primitive-coverage.md`](../../docs/designs/ide-primitive-coverage.md) for the per-tool survey. Hooks are reminders/context, not autonomous execution — skilldrop skills are agent instructions, so the hook prompts *you* to run the review, it doesn't silently run an AI pass. `skilldrop uninstall` removes any hook artifacts it wrote. Vocabulary and the per-target mapping are in the RFC.

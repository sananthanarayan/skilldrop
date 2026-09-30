---
title: From story to merged code — the dev-team workflow
summary: A complete dev-team session: split the story, implement with checkpoints, gate with the review panel, document what shipped.
kind: tutorial
---

# From story to merged code — the dev-team workflow

Four skills, one sequence. The point is the gates — every handoff has a check, and nothing moves forward until the check passes.

Install everything up front:

```bash
npx skilldrop-cli install --pack dev-team --panel review
```

`--panel review` installs the three reviewer subagents (`devils-advocate`, `security-reviewer`, `code-quality`) alongside the `pre-merge-review` orchestrator that fires them in parallel.

---

## Step 1 — Split the story

**Skill:** `user-story-splitter`

A vague story produces a vague implementation. `user-story-splitter` breaks one story into vertical slices — each independently deployable, each with its own acceptance criteria. Nothing here writes code; the output is a list of stories each small enough to implement and review in a single session.

**Say:** *"Split this story into implementable slices with acceptance criteria: [paste story]"*

**Gate:** Each slice must have a testable acceptance criterion. A slice without one is sent back.

---

## Step 2 — Implement

**Skill:** `feature-implement-loop`

The build loop: plan → implement → checkpoint → repeat. At each checkpoint the skill pauses, shows what was built, and asks whether to continue. The loop has a cap (default 3 iterations) — not because the skill runs out of ideas, but because a loop that runs forever is a loop without a gate. When the cap is reached, the work is either done or the story needs to be split further.

**Say:** *"Run the feature-implement-loop on this slice: [paste the slice from step 1]"*

**What each checkpoint checks:**
- Does the implementation satisfy the acceptance criterion?
- Are there tests?
- Is there anything the next reviewer cannot see from the diff alone?

If a checkpoint fails its own check, the loop re-runs from that point — not from the beginning.

---

## Step 3 — Review

**Skill:** `pre-merge-review`

Fires `devils-advocate`, `security-reviewer`, and `code-quality` in parallel. Each runs a separate pass; their findings are merged into one report. Nothing merges until all three pass.

**Say:** *"Run a pre-merge review on the changes in this branch"*

**What each reviewer checks:**
- `devils-advocate` — correctness; logic errors, missing edge cases, broken contracts
- `security-reviewer` — exploitability; injection, auth, secrets, data exposure
- `code-quality` — craft; naming, duplication, test coverage, dead paths

A finding from any reviewer is a blocking issue. The report shows which reviewer raised it so fixes are targeted, not re-reviewed from scratch.

---

## Step 4 — Document

**Skill:** `release-notes`

`release-notes` writes the entry for what shipped — user-facing language, no implementation detail, grounded in the diff and the acceptance criteria from step 1.

**Say:** *"Write release notes for this change: [paste the story and a summary of what was built]"*

The output is a changelog entry ready to paste. It does not describe how the feature works internally; it describes what a user can now do.

---

## The full run

```
user-story-splitter → [for each slice] feature-implement-loop → pre-merge-review → release-notes
```

The review panel is the gate between implementation and merge. A story that does not pass all three lenses does not ship — not because the rule says so, but because the three lenses catch different things and none of them is redundant.

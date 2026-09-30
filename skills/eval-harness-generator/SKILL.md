---
name: eval-harness-generator
description: Takes a skill's SKILL.md and generates a set of eval cases — trigger queries, expected output shape, and pass/fail criteria — ready to drop into the skill's evals/ directory. Use when adding evals to a new or existing skill, verifying a skill behaves as documented, or building a regression gate before modifying a skill.
---

# eval-harness-generator

Reads a SKILL.md and generates eval cases that cover the skill's happy path, edge cases, and known failure modes. The output is JSON that drops directly into `skills/<name>/evals/cases.json`. Unlike `llm-eval-harness` (which designs eval harnesses for arbitrary LLM features), this skill specifically targets the skilldrop eval format and the patterns that skilldrop skills routinely get wrong.

## How to respond

### Step 1 — Read the skill

Ask the user to paste the full SKILL.md. Extract:
- What the skill takes as input
- What the skill produces as output
- Any explicit quality bars or anti-patterns the skill names
- Whether the skill is a **gate** (emits a verdict from `contracts/terminals.json`) or a **generator** (produces an artifact)

### Step 2 — Identify failure modes

Before writing cases, enumerate the failure modes the eval set should catch:

| Category | Failure mode to test |
|---|---|
| **Happy path** | Standard input produces the expected artifact/verdict |
| **Minimal input** | Sparse or ambiguous input — does the skill ask clarifying questions rather than hallucinate? |
| **Anti-pattern input** | Input that would tempt the skill to produce a common bad output (named in the SKILL.md's quality bar) |
| **Edge input** | Boundary conditions specific to this skill (e.g., a bug report with no repro steps for bug-triage) |
| **Gate refusal** | For gate skills: input that should produce BLOCKED or REVISE, not PROCEED |

### Step 3 — Generate the eval cases

Produce a JSON array with 8–12 cases. Each case:

```json
{
  "id": "happy-path-standard",
  "trigger": "The exact query or input that activates this case",
  "expected_shape": [
    "Output contains a <specific element>",
    "Output names a specific field or section",
    "Output avoids <anti-pattern named in quality bar>"
  ],
  "must_not_include": [
    "Fabricated detail not present in the input",
    "A verdict word from the wrong class (for gate skills)"
  ],
  "verdict_class": "pass",
  "notes": "One sentence on what this case is testing and why it matters"
}
```

For gate skills, use `verdict_class` values from `contracts/terminals.json`: `pass`, `conditional`, `revise`, `redirect`, `blocked`. For generators, use `pass` / `fail`.

### Step 4 — Write an eval strategy note

After the JSON array, add a brief eval strategy note (3–5 sentences) explaining:
- Which cases cover which failure modes
- The most important case and why
- What a regression on which case would mean

### Step 5 — Remind about placement

Tell the user:
```
Drop this into skills/<skill-name>/evals/cases.json
Run: python3 validate.py   # confirms the file is found
```

## Anti-patterns

- **Triggers that don't test anything.** "Run the skill on this input" is not a meaningful trigger. Each trigger must be specific enough that a failing model would produce a wrong output you'd recognize.
- **expected_shape items that can't be checked.** "Output is comprehensive" is not checkable. Name specific sections, fields, or behaviors.
- **Missing anti-pattern cases.** The most common eval gap is no cases that test the quality bar's failure modes. If a skill says "never present a hypothesis as the cause," there must be a case where the input tempts that failure.

For designing eval harnesses for general LLM features (not skilldrop skills specifically), use `llm-eval-harness` instead. Use `contribution-wizard` when creating a new skill from scratch — it calls this skill as part of the authoring flow.

## Quality bar

- **Triggers must be realistic.** A trigger of "run this skill" is not an eval case — it doesn't test anything specific. Each trigger should be the kind of input a real user would paste.
- **expected_shape items must be checkable.** "Output is good" is not checkable. "Output contains a numbered repro sequence starting from a clean state" is.
- **Cover the refusal cases.** The most common gap in skilldrop evals is missing cases for the skill's anti-patterns — the bad outputs the quality bar explicitly forbids. At least 2 of the 8–12 cases must test that the skill refuses or avoids its stated failure mode.
- **Don't pad to 12.** Eight strong cases beat twelve weak ones. Only add cases that test a distinct failure mode not already covered.

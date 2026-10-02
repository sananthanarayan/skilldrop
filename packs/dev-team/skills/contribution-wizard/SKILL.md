---
name: contribution-wizard
description: Guides an author through creating a new skilldrop skill from scratch — generates the manifest, SKILL.md, eval cases, and skill-catalogue entry from a plain-language description of the skill's purpose. Use when authoring a new skill for this repo or a private fork, ensuring a new skill meets the schema and validation requirements before submission.
---

# contribution-wizard

Walks an author through the full arc of creating a new skilldrop skill: intake → manifest + SKILL.md + evals + skill-catalogue entry. The output is copy-paste-ready — the author drops the files into `packs/<pack>/skills/<name>/` and runs `python3 validate.py` to confirm before opening a PR.

## How to respond

**Four rules come before the steps and outrank them:**

- **Answer what was asked, first.** Open with the answer, the decision or the artifact, in plain words. Scores, matrices, frameworks and tags come after it, and anything that doesn't change the answer is cut.
- **Use only what you were given.** Don't add facts, names, numbers, incidents, history, steps or sections the input doesn't contain. What you need and don't have is left out of the artifact and listed once at the end under "To confirm".
- **Deliver from what you have.** When the request gives you something to work on, state your assumptions in a line and produce the result. When it gives you nothing to work on, ask for it in one or two plain sentences and say what you will do once you have it.
- **Write for someone who has never heard of this skill.** No skill names, no paths or scripts from this folder, no internal terms, and nothing about how the run was set up. A next step is one plain sentence at the end that describes the work.
- **For this skill:** Read the target repository first: its contributing guide, its agent instructions and two existing skills. Follow the conventions you find, and produce every file that repository requires for a submission, not a generic skill.

### Step 1 — Intake (ask all at once)

Ask these questions in a single block — not one at a time:

> **New skill intake**
>
> 1. **Purpose**: what does this skill do in one sentence?
> 2. **Input**: what does the agent receive? (paste, file, structured data, conversational context)
> 3. **Output**: what does the agent produce? (artifact type, format, length)
> 4. **Pack**: which role pack does it belong to? (solution-architect / product-manager / dev-team / sre-oncall / stakeholder-comms / ai-engineering / api-builder / new pack)
> 5. **Is it a gate?** Does it emit a pass/fail verdict, or generate an artifact?
> 6. **Related skills**: which existing skills does it complement or hand off to?
> 7. **External deps**: does it need API keys, npm packages, or pip libraries?

### Step 2 — Generate all artifacts in one response

After intake, produce the following in a single response, each in its own fenced code block:

#### `manifest.json`

```json
{
  "name": "<kebab-case-name>",
  "version": "1.0.0",
  "description": "<use-case-first description — what it does, then trigger phrases>",
  "entrypoint": "SKILL.md",
  "deps": { "npm": [], "pip": [] },
  "env": { "required": [], "optional": [] },
  "related": ["<related-skill-1>", "<related-skill-2>"],
  "tags": ["<tag1>", "<tag2>"],
  "model": {
    "tier": "<light|standard|heavy>",
    "rationale": "<one sentence: why this tier fits what the skill does>"
  }
}
```

If the skill ships `scripts/`, add a `permissions` block before `model`: the hosts the scripts contact, the external programs they run, and where they write (`"none"`, `"named-paths"`, `"project"` or `"anywhere"`). For example: `"permissions": { "network": [], "commands": ["pdftotext"], "files": "named-paths" }`. Validation fails a script skill without it, and fails one whose code does something it doesn't declare.

Tier guidance:
- **light**: pattern matching, formatting, extraction with no judgment calls
- **standard**: synthesis, judgment calls, structured output requiring reasoning (most skills)
- **heavy**: multi-step reasoning with high stakes or adversarial review (gates, threat models)

#### `SKILL.md`

```markdown
---
name: <skill-name>
description: <same as manifest description>
---

# <skill-name>

<One paragraph: what this skill does and why it's useful. Name the problem it solves.>

## How to respond

<Numbered steps. Each step is an observable action. No vague "reason about X" steps.>

## Quality bar

<Three to five bullet points: what a good output includes and what it never does. Name anti-patterns explicitly.>
```

#### `evals/cases.json`

Eight eval cases covering: 2 happy-path, 2 minimal/edge input, 2 anti-pattern (the quality bar failures), 2 refusal or boundary cases. Format:

```json
[
  {
    "id": "happy-path-standard",
    "trigger": "<realistic input>",
    "expected_shape": ["<checkable criterion 1>", "<checkable criterion 2>"],
    "must_not_include": ["<anti-pattern from quality bar>"],
    "verdict_class": "pass",
    "notes": "<one sentence on what this tests>"
  }
]
```

#### Skill catalogue entry

One row for `guides/reference/skill-catalogue.md`, under the right category, matching the format of existing rows:

```
| [`<skill-name>`](../../packs/<pack>/skills/<skill-name>/SKILL.md) | <One sentence describing what the skill does and the output it produces.> |
```

#### Pack and outcome

State which one pack the skill belongs in (`core` only if every role needs it) — its folder goes at `packs/<pack>/skills/<skill-name>/` — and which `outcomes` entry in `catalogue.json` to add it to.

### Step 3 — Install check reminder

After generating, tell the author:

```
Next steps:
1. mkdir -p packs/<pack>/skills/<skill-name> && cd packs/<pack>/skills/<skill-name>
2. Drop in manifest.json, SKILL.md, and evals/cases.json
3. python3 validate.py    # must pass before opening a PR
4. Add the row to guides/reference/skill-catalogue.md under the correct category
5. Add the skill to an outcome in catalogue.json
6. If the skill has a how-to guide, add it to guides/how-to/ and guides/README.md
```

## Anti-patterns

- **Generating manifests without checking the schema.** The most common contribution failure is a manifest missing a required field. Always instruct the author to run `python3 validate.py` before opening a PR.
- **Generating eval triggers that test nothing.** "Run this skill" is not an eval case. Insist on realistic triggers that would expose a specific failure mode if the model got it wrong.
- **Listing related skills that don't exist.** A manifest that references a non-existent skill fails validation. Instruct the author to run `ls skills/` before finalizing the `related` array.

After generating eval cases, the author can use `eval-harness-generator` to add more coverage or to regenerate cases after modifying the SKILL.md.

## Quality bar

- **Manifests must be schema-valid.** Every field required by `contracts/skill.schema.json` must be present. Use `python3 validate.py` as the check — not a visual review.
- **Eval triggers are realistic.** A trigger of "use this skill" is not an eval case. Each trigger should be a plausible user input, not a test harness artifact.
- **SKILL.md has observable steps.** Every step in "How to respond" must describe an action the agent takes — never "think about X" or "consider Y".
- **The quality bar names anti-patterns.** A quality bar that only says what good looks like doesn't help the agent avoid common failures. Name at least two things the output must never do.
- **Related skills are real.** Every skill listed in `related` must exist in the skills directory. Run `ls skills/` to check before outputting.

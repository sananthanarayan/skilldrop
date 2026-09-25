---
title: Author a new loop
summary: How to add a loop — the closed loop.json contract, the three stage types, gate rules, and the checks that will reject a loop that only looks like governance.
kind: how-to
---

# Author a new loop

A loop is a **sequence over skills that already exist**. Write one when the order and the
gates between existing skills are the thing worth shipping; write a skill when a new artifact
is. A loop that needs a skill nobody has written yet is blocked on that skill.

Full rules and the pre-commit checklist live in [AGENTS.md](../../AGENTS.md); the design
rationale is [RFC-0028](../../docs/rfcs/0028-loops-as-a-primitive.md).

## 1. Write the RFC

`loops/` is a primitive, so adding to it is a structural decision. Copy
[`docs/rfcs/0000-template.md`](../../docs/rfcs/0000-template.md) to the next number and mark
it `accepted` before building.

## 2. Write `loop.json`

The contract is [`contracts/loop.schema.json`](../../contracts/loop.schema.json) and it is
**closed** — an unknown key fails, it is not ignored.

```json
{
  "name": "build",
  "description": "Use-case-first. What the loop delivers, then the trigger phrases an agent matches on.",
  "entrypoint": "LOOP.md",
  "kind": "loop",
  "cap": 3,
  "stages": [
    { "id": "implement", "type": "generate", "intent": "One line.", "skills": ["feature-implement-loop"] },
    { "id": "verify", "type": "verify", "intent": "One line.", "skills": ["pre-merge-review"],
      "gate": { "id": "G2", "kind": "mechanical",
                "script": "skills/pre-merge-review/scripts/gate.py",
                "verdicts": ["READY", "NOT READY", "BLOCKED"],
                "revise_to": "implement" } }
  ]
}
```

- `kind` is `loop` (advances toward a terminal) or `wrapper` (its middle stage is any
  generator, chosen at run time — only a wrapper may use `"*"` in `skills`).
- `type` is `generate` / `verify` / `gate` — the three states
  [`agent-loop-design`](../../skills/agent-loop-design/SKILL.md) mandates.
- `cap` bounds revision rounds. Default 3.

## 3. Get the gates right

This is where a loop is won or lost. A gate that cannot fail is decoration.

- **`id`** is repo-unique (`G2`, `G2.1`) — a gate is a place people point at in review.
- **`kind`**: `mechanical` needs a real `script` whose exit code decides; `review` and `human`
  must **not** have one.
- **`verdicts`** must all exist in
  [`contracts/terminals.json`](../../contracts/terminals.json). A gate may not invent a new
  word for an outcome that already has one.
- Every gate needs **at least one pass-class verdict and at least one non-pass**, and must be
  able to emit **`BLOCKED`** — a required input can always be missing.
- **`revise_to`** must name an **earlier** stage.

## 4. Write `LOOP.md`

Frontmatter `name` + `description` must match `loop.json` exactly. Then: the stage table, how
to run it, the verdicts, what to do when a stage's skill is not installed, and the same
`Quality bar` + `Anti-patterns to avoid` sections a skill ships. A `LOOP.md` without those two
is a diagram.

## 5. Register and generate

- Add the loop to at least one pack's `loops` array in [`packs.json`](../../packs.json).
- **Do not** add it to `model-routing.json` — a loop sequences skills and makes no model call
  of its own, so it carries no tier.
- Run `python3 build_loops.py` to regenerate `docs/loops/<name>.mmd` and the README's Mermaid
  block. Both are generated; editing either by hand fails a check.
- Add a row for it in the README — `validate.py` requires one.

## 6. Check it

```bash
python3 validate.py
node bin/skilldrop.js validate
python3 build_loops.py --check
```

Then install it into a clean session and run it on a realistic input:

```bash
node bin/skilldrop.js install --loop <name> --dest /tmp/try
```

Confirm each stage advances only through its gate, that the cap is honoured, and — the
invariant everything rests on — that a single skill from the loop still runs standalone when
installed on its own.

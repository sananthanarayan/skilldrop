---
title: The loop contract
summary: Every rule a new loop must meet — the closed loop.json fields, the three stage types, gate ids and verdicts, what LOOP.md carries, and how a loop is registered and checked.
kind: reference
---

# The loop contract

This page is the detail behind [Author a new loop](../how-to/author-a-loop.md). The full rules and
the pre-commit checklist are in [AGENTS.md](../../AGENTS.md); the design rationale is
[RFC-0028](../../docs/rfcs/0028-loops-as-a-primitive.md).

## When a loop is the right thing

A loop is a **sequence over skills that already exist**. Write one when the order and the gates
between existing skills are the thing worth shipping; write a skill when a new artifact is. A
loop that needs a skill nobody has written yet is blocked on that skill.

Loops are a primitive, so adding one is a structural decision: it starts with an RFC copied from
[`docs/rfcs/0000-template.md`](../../docs/rfcs/0000-template.md) to the next number, marked
`accepted` before building.

## `loop.json`

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
                "script": "packs/dev-team/skills/pre-merge-review/scripts/gate.py",
                "verdicts": ["READY", "NOT READY", "BLOCKED"],
                "revise_to": "implement" } }
  ]
}
```

| Field | Rule |
|---|---|
| `name`, `description` | `description` is use-case-first, with trigger phrases at the end. |
| `version` | `MAJOR.MINOR.PATCH`, required. Bump it whenever `LOOP.md` or `loop.json` changes: `skilldrop update` refreshes an installed loop only when its version moves. |
| `entrypoint` | `"LOOP.md"`. |
| `kind` | `loop` advances toward a terminal; `wrapper` has a middle stage that is any generator, chosen at run time. Only a wrapper may use `"*"` in `skills`. |
| `cap` | Bounds revision rounds. Default 3. |
| `stages[].type` | `generate`, `verify` or `gate` — the three states [`agent-loop-design`](../../packs/ai-engineering/skills/agent-loop-design/SKILL.md) mandates. |
| `stages[].skills` | Real skill folder names. |

## Gates

This is where a loop is won or lost. A gate that cannot fail is decoration.

- **`id`** is repo-unique (`G2`, `G2.1`) — a gate is a place people point at in review. It reads
  in lifecycle order: the whole number is the loop's place (`discover` G0 through `operate` G4;
  G5 and up are the loops outside it, in the order they were added), and a decimal is a second gate in the same
  loop (RFC-0044).
- **`kind`**: `mechanical` needs a real `script` whose exit code decides; `review` and `human`
  must **not** have one.
- **`verdicts`** must all exist in
  [`contracts/terminals.json`](../../contracts/terminals.json). A gate may not invent a new
  word for an outcome that already has one.
- Every gate needs **at least one pass-class verdict and at least one non-pass**, and must be
  able to emit **`BLOCKED`** — a required input can always be missing.
- **`revise_to`** must name an **earlier** stage.

## `LOOP.md`

- Frontmatter `name` + `description` match `loop.json` exactly.
- The body carries the stage table, how to run it, the verdicts, what to do when a stage's skill
  is not installed, and the same `Quality bar` + `Anti-patterns to avoid` sections a skill
  ships. A `LOOP.md` without those two is a diagram.
- A `## Run log (opt-in)` section, copied from any existing loop with the example line changed
  to your loop's name and first gate. `validate.py` requires it, so `skilldrop loop-stats` can
  read every loop the same way ([Measure your loops](../how-to/measure-your-loops.md)).
- On install, `LOOP.md` projects to `<dest>/<name>/SKILL.md`, so a loop's name may not collide
  with a skill's.

## Registration

- The loop lives in exactly one pack: `packs/<pack>/loops/<name>/`. That pack, together with
  `core`, must hold every skill the loop's stages run.
- **Do not** add it to `model-routing.json` — a loop sequences skills and makes no model call of
  its own, so it carries no tier. `validate.py` fails one that is there.
- Add a row for it to the table in [the loops reference](loops.md), and a pair of
  `<!-- loop:<name>:start -->` / `<!-- loop:<name>:end -->` markers where its diagram goes.
- Give it its lines in `build_loops.py`'s `LIFECYCLE` (a stage) or `OUTSIDE` (anything else): a
  heading, when to start, and what it ends with. The
  [operating model](../explanation/operating-model.md) picture is drawn from them, and
  `python3 build_loops.py --check` fails until a new loop has them.
- `python3 build_loops.py` regenerates `docs/loops/<name>.mmd`, the reference's Mermaid block and
  `docs/loops/operating-model.svg`. All three are generated; editing one by hand fails a check.

## Checks

```bash
python3 validate.py
node bin/skilldrop.js validate
python3 build_loops.py --check
```

`validate.py` runs the `build_loops.py` drift check as well. After the checks pass, install the
loop into a clean session (`node bin/skilldrop.js install --loop <name> --dest /tmp/try`) and run
it on a realistic input. Confirm each stage advances only through its gate, that the cap is
honoured, and — the invariant everything rests on — that a single skill from the loop still runs
standalone when installed on its own.

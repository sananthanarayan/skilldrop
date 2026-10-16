---
title: Author a new loop
summary: How to add a loop — the closed loop.json contract, the three stage types, gate rules, and the checks that will reject a loop that only looks like governance.
kind: how-to
---

# Author a new loop

You can add a loop that runs skills already in the catalogue in a fixed order, with a gate
between stages that decides when work moves on.

Write a loop when the order and the gates are the thing worth shipping; write a skill when a new
artifact is. Every field and gate rule is on [The loop contract](../reference/loop-contract.md).

## Write the RFC

Loops are a primitive, so start from the RFC template and mark the copy `accepted` before you
build.

```bash
cp docs/rfcs/0000-template.md docs/rfcs/NNNN-<slug>.md
```

The RFC records why this sequence deserves to be a loop and which skills it runs.

## Create the loop folder

Put the loop in the one pack that, with `core`, holds every skill its stages run.

```bash
mkdir -p packs/<pack>/loops/<name>
```

In it, write `loop.json` against the closed contract: stages typed `generate`, `verify` or
`gate`, and gates numbered by the loop's place in the lifecycle, from `G0` for `discover`.

## Write LOOP.md from an existing loop

Read a shipped loop and copy its shape, including the `## Run log (opt-in)` section with the
example line changed to your loop's name and first gate.

```bash
cat packs/dev-team/loops/build/LOOP.md
```

Your `LOOP.md` repeats `loop.json`'s `name` and `description` exactly and ships a `Quality bar`
and `Anti-patterns to avoid` section, like a skill.

## Draw the loop into the operating model

Give the loop its lines in `build_loops.py`'s `LIFECYCLE` (a stage) or `OUTSIDE` (anything else),
add its row and diagram markers to [the loops reference](../reference/loops.md), then regenerate.

```bash
python3 build_loops.py
```

It writes `docs/loops/<name>.mmd`, the reference's Mermaid block and the
[operating model](../explanation/operating-model.md) picture.

## Check the loop

Run the repo's lint from the root.

```bash
python3 validate.py
```

It fails a loop that breaks the contract, sits in `model-routing.json`, or is missing from the
diagrams.

## Run it in a clean session

Install the loop into a scratch directory and run it on a realistic input.

```bash
node bin/skilldrop.js install --loop <name> --dest /tmp/try
```

Each stage should advance only through its gate, the cap should hold, and any one of its skills
should still run when installed on its own.

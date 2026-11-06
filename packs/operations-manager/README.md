# Operations manager

Staff rotas from who is available, what each shift needs and the working-time rules: a week or fortnight built and drawn as a grid, shown only once a script has checked every shift's cover and skills, and every person's hours, rest between shifts and days in a row.

`/plugin install operations-manager@skilldrop` · generated from [`main`](https://github.com/sananthanarayan/skilldrop) — do not edit.

## Start here: Get next week's rota, with every shift covered and nobody short of rest

Paste this into Claude Code:

```text
Make next week's rota for the café, Monday to Saturday. Every day: an opening shift 06:30–14:30 and a closing shift 14:00–21:00, each needing one keyholder and one barista. Staff: Amira (keyholder, barista, max 40 h), Ben (barista, max 24 h, not Wednesdays), Chloe (keyholder, barista, max 32 h), Dev (keyholder, barista, max 40 h), Ema (barista, max 24 h, not Mondays or Tuesdays), Fay (barista, max 32 h). At least 11 hours between shifts, nobody more than 5 days in a row.
```

- **Before you start:** Who works for you, what they can do, and when they can't work
- **Before you start:** The shifts you need covered, with how many people of each kind
- **Before you start:** Python 3 on the machine, which the rota check and week drawing run on
- **How to tell it worked:** shift-roster leads with the rota as a table of days by people, says which shifts it couldn't fill and why, lists the rules it assumed, and saves a week grid drawn from a check that found every shift covered and no rest, hours or consecutive-day rule broken.
- **If nothing happens:** If shift-roster does not activate, ask for it by name ("use shift-roster"). If it says a week can't be covered, it names the smallest change that would; give it that change or say which rule may bend.

## Loops

- `ship-a-draft`

## Skills

- `brief-intake`
- `context-graph`
- `council-review`
- `doc-critique`
- `output-hygiene`
- `shift-roster`

More: https://sananthanarayan.github.io/skilldrop/packs/operations-manager/

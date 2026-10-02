# Stakeholder comms

Non-technical audiences: audience profiling, exec summaries, decision logs, and guides. Decks live in the design pack.

`/plugin install stakeholder-comms@skilldrop` · generated from [`main`](https://github.com/sananthanarayan/skilldrop) — do not edit.

## Start here: Turn a long document into a one-page summary for leadership

Paste this into Claude Code:

```text
Turn this design doc into a one-page executive summary for our steering committee: <paste the doc>.
```

- **How to tell it worked:** exec-summary returns a one-page summary that a time-poor reader can act on in 30 seconds, written without jargon.
- **If nothing happens:** If exec-summary does not activate, ask for it by name ("use exec-summary") and check that its folder exists in your skills folder (`~/.claude/skills/` by default).

## Loops

- `ship-a-draft`

## Skills

- `audience-profile`
- `brief-intake`
- `council-review`
- `decision-log`
- `doc-critique`
- `exec-summary`
- `guide-builder`
- `output-hygiene`

More: https://sananthanarayan.github.io/skilldrop/packs/stakeholder-comms/

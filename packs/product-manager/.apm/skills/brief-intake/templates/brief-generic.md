# Brief: Generic

> Target downstream skill: _unknown_ — emit this when the user hasn't picked a next step yet.

This is the fallback shape. It's a superset of the most useful fields across all targets — the user (or you, next turn) picks the downstream skill and the relevant fields move into its specific brief.

## One-line summary
{What is this about?} [explicit|implied|inferred|missing]
> "{verbatim snippet}"

## Type of artifact the user might want next
{Best guess based on the source — and why}
- {e.g. "Looks like a decision being captured → adr-generator"}
- {e.g. "Looks like a runbook brief — service name + on-call mentioned"}

## Subject
- **What it's about (object):** {service / decision / project / vendor selection} [explicit|implied|inferred|missing]
- **Who's involved:** {teams, people, customers} [explicit|implied|inferred|missing]
- **Why now:** {forcing function if any} [explicit|implied|inferred|missing]

## Key facts (load-bearing)
- {Fact 1 — quote} [explicit|implied|inferred|missing]
- {Fact 2}
- {Fact 3}

## Decisions / asks present in the source
- {Anything that looks like a decision or an ask} [explicit|implied|inferred|missing]

## Open questions / unknowns
- {Things explicitly unresolved in the source} [explicit|implied|inferred|missing]

## Dates / deadlines
- {Date → what it's tied to (absolute, with `(implied)` if computed)} [explicit|implied|inferred|missing]

## Names / owners
- {Name → role / responsibility} [explicit|implied|inferred|missing]

## Numbers / metrics
- {Number → what it measures} [explicit|implied|inferred|missing]

---

## 🚩 Next step
Pick a downstream skill, then run `brief-intake` again with that target to get the precisely-shaped brief. Suggested:
- {Skill name} — because {reason from this source}

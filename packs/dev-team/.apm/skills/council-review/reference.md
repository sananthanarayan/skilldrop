# council-review — reference

Facilitation guidance that doesn't fit in `SKILL.md`. This is the "how to chair well" material.

## Choosing the roster

Always seat the five standing seats. Then add bench seats by what the change *touches*, not by what sounds thorough:

| If the change… | Seat |
|---|---|
| has a hot path / query / loop over user-sized data | ⚡ Performance |
| provisions infra, adds a service, or fans out API/LLM calls | 💸 Cost |
| changes schema, backfills, or touches persisted state | 🗄 Data & Migration |
| renders user-facing UI | ♿ Accessibility |
| touches PII / regulated data / licenses / audit | 📋 Compliance |

**Bench the rest explicitly.** "Benched: Cost (no infra change), A11y (no UI)" tells the reader you considered and dismissed them — that's signal, not omission. Seating a member who then has nothing to say is the inflated-roster anti-pattern.

A small, clean change might legitimately produce four abstentions and one 🟢. That's a fine outcome — don't pad it.

## Finding the real cruxes (the skill's core craft)

A crux is **not** just "two seats disagree." It's a disagreement that turns on something specific. Pressure-test each apparent conflict:

1. **Is it real, or a misunderstanding?** Often two seats are talking past each other (Security means "exploitable," Pragmatist heard "theoretically imperfect"). Resolve those silently — they're not cruxes.
2. **What does it turn on?** Force it to one of two kinds:
   - **A tradeoff** — both seats are right, they value different things (durability vs latency, safety vs speed-to-ship). The Chair must *choose*, and say what's traded.
   - **A missing fact** — the disagreement would evaporate if you knew X (the actual load, whether this is internal-only, the retention requirement). The Chair names X as the thing to go learn.
3. **What resolves it?** Every crux ends with the data, constraint, or decision that settles it. A crux with no resolution path is just venting.

If you find yourself writing a crux where one side has no real point, delete it — you've manufactured conflict.

## How the Chair decides (without averaging)

The Chair is not a vote-counter and not a sixth opinion. The job:

1. **Weight by stakes, not by headcount.** One 🔴 from Security on a live exploit outweighs three 🟢s on convenience. One 🔴 from the Pragmatist ("we don't need this at all") can outweigh everyone's polish notes. Severity and reversibility set the weight.
2. **Resolve each crux explicitly.** For a tradeoff: choose, and name what you're trading away. For a missing fact: decide whether you can proceed without it (with a condition/flag) or must learn it first.
3. **Default toward reversibility.** When genuinely uncertain, prefer the path that's cheap to undo (feature flag, narrow rollout, `/v2`) over the irreversible one (data migration, public API change). This often turns a 🧭 SPLIT into a ⚠️ PROCEED WITH CONDITIONS.
4. **Record the dissent.** The losing seat's strongest point goes on record with what to watch. This is not politeness — it's the tripwire for "what would change our mind."
5. **Make the verdict falsifiable.** "What would change our mind" names the future fact that flips the decision. Without it, the verdict is an opinion; with it, it's a decision the team can revisit when reality moves.

### When to use SPLIT
Reserve 🧭 SPLIT for a true deadlock on a tradeoff where the deciding fact is genuinely a business/product call above the council's authority (e.g. "is a 2-hour RTO acceptable for this tier?"). Even then, the Chair states a **lean** and the **single question** the human must answer. A Chair that reaches for SPLIT to avoid deciding is failing — most apparent deadlocks resolve via reversibility (rule 3).

## Running a pre-mortem with the council

For "assume this shipped and caused an incident — what happened?", flip each seat from *reviewer* to *forecaster*:
- Each seat names the **most likely failure in its domain** and a leading indicator for it.
- The cruxes become "which failure is most probable / most expensive."
- The verdict becomes a **prioritized watch-list**: the top 2–3 failure modes, each with the cheapest mitigation or the metric that gives early warning.

Same seats, same discipline, future tense.

## Keeping seats distinct (the overlap test)

If two seats make the same point, the roster is wrong. Common overlaps and who owns what:

| Overlap | Owner | The other seat…|
|---|---|---|
| "migration can't roll back" | 🗄 Data (correctness of the migration) | 🛠 Operator defers, or speaks to deploy/downtime only |
| "this is a DoS" | 🔒 Security (it's an attack) | ⚡ Performance defers |
| "premature generalization" | shared 🏛 Architect (design) + ⚖️ Pragmatist (need) — **state it as consensus**, not two findings |
| "logs sensitive data" | 📋 Compliance (obligation) + 🔒 Security (exposure) — coordinate: one names the law, one names the attack |

When two seats genuinely converge, that's a *stronger* signal — present it as "Architect and Pragmatist agree," not as two separate bullet points padding the count.

## Relationship to the single-voice skills

The council is heavier than the focused reviewers — use it when the multi-disciplinary tension is the point, not as a default. Rules of thumb:
- One adversarial pass on just-written code → [`devils-advocate`](../devils-advocate/SKILL.md).
- One rubric pass on a doc → [`doc-critique`](../doc-critique/SKILL.md).
- Score named options on weighted criteria → [`tech-comparison-matrix`](../tech-comparison-matrix/SKILL.md).
- A decision/design/change where security, ops, maintainability, delivery, and correctness pull in different directions → **council-review**.

Don't chain these internally (per the repo's no-internal-chaining rule). A human runs the council, then hands a specific finding to `devils-advocate` if they want it drilled.

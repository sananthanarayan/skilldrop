# Council review: {what's being decided / PR title}
_Scope: {decision · design · code change} · {N files / the question} · Reviewed: {YYYY-MM-DD}_

## Verdict

**{✅ PROCEED · ⚠️ PROCEED WITH CONDITIONS · 🔁 REVISE · ⛔ RECONSIDER · 🧭 SPLIT}**

{2–4 sentences. Lead with the decision. Name the **tradeoff being chosen** and what it trades away. If conditions, they're listed below. This is the only paragraph most readers will read — make it carry the decision.}

**Tradeoff chosen:** {e.g. "We accept added operational load for a load-bearing security gain."}
**What would change our mind:** {the fact/event that should trigger a revisit, e.g. "if export volume exceeds 1k/min, the Operator's stall risk becomes blocking — revisit."}

### Conditions (if PROCEED WITH CONDITIONS / REVISE)
1. {concrete, checkable — "parameterize the query at users.ts:142"}
2. {…}

## The vote

| Seat | Stance | One-line position |
|---|---|---|
| 🏛 Architect | 🟢/🟡/🔴/⚪ | {…} |
| 🔒 Security | 🟢/🟡/🔴/⚪ | {…} |
| 🛠 Operator | 🟢/🟡/🔴/⚪ | {…} |
| ⚖️ Pragmatist | 🟢/🟡/🔴/⚪ | {…} |
| 👤 User-Advocate | 🟢/🟡/🔴/⚪ | {…} |
| {⚡ Performance — bench, seated because …} | 🟢/🟡/🔴/⚪ | {…} |

_Benched: {Cost, Data, A11y, Compliance} — {one-line why each was not relevant}._

## Cruxes (where the council genuinely split)

> If the council substantively agreed, replace this section with: **"Consensus — {the one shared reason}."** Do not manufacture cruxes.

### Crux 1 — {short name, e.g. "Durability vs delivery speed"}
- **Split:** {Operator 🔴 vs Pragmatist 🟢}
- **Turns on:** {the real tradeoff or the missing fact — "we don't know the p99 write volume"}
- **Resolves with:** {the data/constraint/decision that breaks the tie}

### Crux 2 — {…}

## Positions (the detail behind the vote)

### 🏛 Architect — {stance}
- {concrete point + `file:line` / named assumption}

### 🔒 Security — {stance}
- {…}

### 🛠 Operator — {stance}
- {…}

### ⚖️ Pragmatist — {stance}
- {…}

### 👤 User-Advocate — {stance}
- {…}

## Dissent on record
{The strongest minority point, preserved. Who held it, and what they'd want watched. Not erased just because the verdict went the other way — this is what the team re-reads when "what would change our mind" comes true.}

---
name: council-review
description: Convene a council of distinct senior-engineer personas (Architect, Security, Operator/SRE, Pragmatist, User-Advocate, plus optional bench seats) to deliberate a decision, design, or code change — each takes an independent stance, the genuine disagreements are surfaced as named cruxes, and a Chair issues a reconciled verdict that records dissents and states what would change the decision. The "Claude Council." Use when a choice has real tradeoffs and one reviewer's voice isn't enough: architecture decisions, risky changes before merge, RFC/design scrutiny, "should we adopt X?", rewrite-vs-refactor, or a pre-mortem.
---

# council-review

You convene a **council of distinct expert personas** to deliberate something consequential, then reconcile their views into a decision. The value is not five voices agreeing — it's **surfacing where senior engineers genuinely disagree, naming the tradeoff at the heart of it, and deciding anyway.**

This is the deliberation counterpart to the single-voice reviewers. Use [`devils-advocate`](../devils-advocate/SKILL.md) when you want one adversarial pass on code, [`doc-critique`](../doc-critique/SKILL.md) for one pass on a doc, [`tech-comparison-matrix`](../tech-comparison-matrix/SKILL.md) for a weighted scoring of named options. Use the **council** when the question is open, the tradeoffs are real, and you need multiple disciplines in the room.

## What the council reviews

Three shapes — the seats apply to all three; their evidence just differs:

| Shape | Example | Evidence a seat cites |
|---|---|---|
| **Decision / question** | "Monolith or services?" · "Adopt Kafka?" · "Rewrite or refactor?" | the specific claim or assumption |
| **Design / RFC** | a design doc, an architecture proposal, an API contract | the section / interface |
| **Code change** | a diff, a PR, a load-bearing module before merge | `file:line` |

If the scope is unclear, ask once which of the three it is. Don't convene a council on the whole repo — the scope is the decision/design/change in front of you.

## The council

Five **standing seats** — each a distinct mandate with a lane it stays in. Read the seat file before speaking for it:

| Seat | Asks | File |
|---|---|---|
| 🏛 **Architect** | Does this fit the system? Right abstraction, coupling, long-term complexity? | [`seats/architect.md`](seats/architect.md) |
| 🔒 **Security Engineer** | What's the threat model? Trust boundaries, data, dependencies? | [`seats/security-engineer.md`](seats/security-engineer.md) |
| 🛠 **Operator (SRE)** | What happens at 3am? Failure modes, rollback, observability, blast radius? | [`seats/operator.md`](seats/operator.md) |
| ⚖️ **Pragmatist** | Is this the simplest thing that works? Over-engineered? Do we even need it? | [`seats/pragmatist.md`](seats/pragmatist.md) |
| 👤 **User-Advocate** | Is it correct for the people who use it? Edge cases, errors, contracts, compat? | [`seats/user-advocate.md`](seats/user-advocate.md) |

Plus a **bench** of optional seats (Performance, Cost/FinOps, Data & Migration, Accessibility, Compliance) — seat them only when the change warrants. See [`seats/bench.md`](seats/bench.md). Chairing and roster-choice guidance that doesn't fit here lives in [`reference.md`](reference.md).

The **Chair** is not a sixth opinion. The Chair facilitates, finds the cruxes, and decides.

## How to respond

1. **Frame the question.** One or two sentences: what's being decided/reviewed, and what "yes" would commit the team to. State the scope shape (decision / design / code). If acceptance criteria or constraints were given, restate them — they're what the seats judge against.

2. **Seat the council.** Always seat the five standing seats. Add bench seats the change clearly warrants (a hot-path change → seat Performance; a schema migration → seat Data & Migration). **State who you seated and who you benched, and why.** A seat with nothing relevant to say should *abstain* (see step 4), not pad the record.

3. **Take each seat's independent position — before any cross-talk.** Independence prevents groupthink. Each seat declares:
   - a **stance**: 🟢 Support · 🟡 Support with conditions · 🔴 Oppose · ⚪ Abstain (out of my lane)
   - **1–3 concrete points** tied to the actual artifact (a `file:line`, a named assumption, a specific interface) — never a generic platitude.
   Keep each seat tight. A seat is not writing a report; it's staking a position with evidence.

4. **Surface the cruxes — this is the most important step.** A *crux* is a specific point where seats genuinely disagree, and the disagreement turns on a real tradeoff or an unresolved fact. For each crux, write:
   - **the split**: who's on each side (e.g. "Operator 🔴 vs Pragmatist 🟢")
   - **what it turns on**: the actual tradeoff ("durability vs delivery speed") or the missing fact ("we don't know the p99 write volume")
   - **what would resolve it**: the data, constraint, or decision that breaks the tie.

   **Do not manufacture cruxes.** If the council substantively agrees, say so plainly and move on — fabricated conflict is the #1 failure of this skill. Real councils often converge; the honest output is sometimes "unanimous, here's why."

5. **Chair's verdict.** The Chair decides — names the tradeoff being chosen and what it trades away. Pick one:

   | Verdict | Meaning |
   |---|---|
   | ✅ **PROCEED** | The council backs it. Minor notes may remain. |
   | ⚠️ **PROCEED WITH CONDITIONS** | Backed *if* the listed conditions are met before merge/commit. |
   | 🔁 **REVISE** | Right direction, but named points must be reworked and re-reviewed. |
   | ⛔ **RECONSIDER** | A blocking problem, or it solves the wrong problem. Don't proceed as-is. |
   | 🧭 **SPLIT** | Genuine deadlock. Rare. The Chair still states a *lean* and the single question that would settle it. |

   The verdict must: (a) name the **tradeoff chosen**, (b) **record dissents** — the strongest minority point, preserved not erased, and (c) state **"what would change our mind"** so the decision is revisitable.

6. **Output** — use [`templates/council-review.md`](templates/council-review.md). Lead with the verdict; readers want the decision first, the deliberation second.

## Quality bar

- **Real disagreement, or honest consensus — never theater.** Manufactured conflict between personas is the cardinal sin. If they agree, say "unanimous" and give the one reason; spend the words on the cruxes that are real.
- **Every seat point is concrete and attached to evidence.** `file:line` for code, the named assumption for a decision. ❌ "Security has concerns." ✅ "Security 🔴: `exec(\`tar ${path}\`)` at jobs/export.ts:28 — `path` is user-controlled; command injection."
- **Stances are explicit and scannable.** The reader sees the split (🟢/🟡/🔴/⚪) at a glance, before reading a word of argument.
- **Seats stay in their lane.** The Pragmatist doesn't relitigate the threat model; Security doesn't lecture on naming. Overlap means the roster is wrong — cut or merge.
- **The Chair decides, doesn't average.** ❌ "There are good points on both sides." ✅ "PROCEED WITH CONDITIONS — we accept the added operational load (Operator's dissent noted) because the security gain is load-bearing; revisit if on-call pages exceed X."
- **Dissent is preserved.** The minority seat's strongest point survives into the verdict. A council that erases dissent is just one opinion wearing five hats.
- **Falsifiable verdict.** "What would change our mind" is mandatory — it turns a verdict into a decision the team can revisit when facts change.

## When to use this skill

- ✅ A consequential decision with real tradeoffs (architecture, build-vs-buy, rewrite-vs-refactor, adopt-this-tool)
- ✅ A risky or load-bearing change before merge, where one reviewer's lens isn't enough
- ✅ An RFC / design doc that needs multi-disciplinary scrutiny (security + ops + maintainability at once)
- ✅ A pre-mortem: "assume this shipped and broke — which seat saw it coming?"

## When NOT to use this skill

- ❌ A trivial or one-line change — convening five voices is noise. Use `devils-advocate` or just review it.
- ❌ A single-lens task. Pure code review → `devils-advocate`. Pure doc review → `doc-critique`. Scoring named options on weighted criteria → `tech-comparison-matrix`.
- ❌ When you need **one** expert answer fast, not a deliberation. The council is for when the disagreement *is* the point.
- ❌ Greenfield spike/throwaway code — deliberation wastes effort on what won't survive.
- ❌ As a rubber stamp to manufacture consensus for a decision already made. If the call is final, don't stage a fake trial.

## Anti-patterns to avoid

- ❌ **Manufactured conflict.** Inventing a 🔴 so the council "looks balanced." If everyone supports it, that's the finding.
- ❌ **Persona cosplay.** Flowery in-character roleplay ("As a battle-scarred SRE, I muse...") over substance. The persona is a *lens*, not a costume.
- ❌ **Groupthink.** Seats echoing each other. Take positions independently (step 3) *before* cross-talk.
- ❌ **A Chair that punts.** "It depends / both have merit" is not a verdict. Decide, name the tradeoff, record the dissent.
- ❌ **Overlapping seats.** Two seats flagging the same issue means the roster is redundant — that's a smell, not thoroughness.
- ❌ **Inflated roster.** Seating eight voices on a small change. Seat what's relevant; bench the rest explicitly.
- ❌ **Reviewing out of scope.** The council deliberates the decision/change in front of it, not the whole codebase's debt.
- ❌ **Burying the verdict.** Leading with the deliberation transcript instead of the decision. Verdict first.

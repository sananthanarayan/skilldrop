---
name: business-case
description: Build a business case for a build/buy/defer investment decision — do-nothing always included as the baseline, benefits quantified as re-runnable calculations with confidence tags, full costs (build + run + opportunity), ranges instead of false precision, and the flip-assumption named. Use when the user needs to justify an investment, write a business case, compare build vs buy vs defer, or get budget/sponsor approval for an initiative.
---

# business-case

Produces the document a sponsor can approve, challenge, or kill on its merits — because every benefit shows its arithmetic, every option includes the one nobody advocates for (doing nothing), and the case names the single assumption that flips the recommendation. Decides *whether to invest*; `tech-comparison-matrix` picks between technologies after, `prd-draft` captures requirements after, `exec-summary` compresses this doc for a board.

## How to respond

1. **Pin the decision and the decider.** What exactly is being decided ("invest ~3 engineer-quarters in X" — not "improve our tooling"), who decides, and by when. Ask at most 2 questions, spent on the **cost of the status quo** ("what does the current state cost per month, in what units?") and the **decision deadline**. A business case without a named decision is an essay.

2. **Always include Option 0: do nothing.** Costed like every other option — the status quo has a price (ongoing pain, growing risk, deferred opportunity) and the case must beat it *explicitly*, not by assumption. Then 2–3 real alternatives (typically build / buy / partial-defer). Every option presented is one someone could genuinely champion; a lineup of two strawmen escorting the preferred option is theater, and reviewers smell it.

3. **Quantify benefits as calculations a reviewer can re-run.** Every benefit shows: the formula, each input with its source tag, and a **confidence tag** (high = measured data, medium = reasonable extrapolation, low = informed guess). ✅ *"40 agents × ~20 min/ticket saved `[data: time study]` × 30 tickets/day → 18–24 FTE-hours/day, confidence: medium (assumes 75–100% of tickets touch the flow)"* — ❌ *"significant efficiency gains"* — an adjective benefit is a benefit that didn't survive arithmetic.

4. **Use ranges, never false precision.** Three estimates multiplied together do not produce "327% ROI" — they produce a range, and the case says which end is likelier and why. State payback as a range too ("breakeven month 7–11"). Single-point outputs from multi-guess inputs are the most reliable sign a case is selling, not informing.

5. **Cost all three layers, per option**: **build** (people × time, the dominant and most-lowballed term — include ramp-up and the integration tail), **run** (infra, licenses, support burden, maintenance — the layer "buy" options hide in year 2+ pricing and "build" options hide in maintenance), and **opportunity** (what these people would otherwise ship — name the displaced thing, don't leave it abstract).

6. **Name the flip-assumption.** The sensitivity question, answered honestly: *which single input, if wrong, reverses the recommendation?* ✅ *"The case rests on ≥60% agent adoption; below ~40%, Option 0 wins — adoption is `[low confidence]`, so we propose a 4-week pilot before full commit."* If no single assumption flips it, say which *pair* does. A case with no flip-condition is claiming certainty it cannot have.

7. **Recommend one option, committally.** The recommendation names the option, the reasoning in two sentences, what was given up (the strongest point of the runner-up, stated fairly), and any de-risking step (pilot, staged commit) tied to the flip-assumption. "It depends" is the analyst's job half-done; the decider can disagree with a recommendation, but they can't disagree with a shrug.

8. **Lead with the ask.** The first lines of the document: the decision requested, the cost, the headline benefit range, the deadline. ✅ *"Ask: approve 3 engineer-quarters (~$210k loaded) for Option B; expected payback month 7–11; decision needed by July 1 to hit Q4 capacity."* Emit with [`templates/business-case.md`](templates/business-case.md), one message.

## Useful references in this skill

- [`templates/business-case.md`](templates/business-case.md) — the skeleton: ask-first structure, option table, benefit-calculation blocks, sensitivity section

## Quality bar

- **Option 0 is present and costed.** A case that doesn't price the status quo hasn't established there's a problem worth money.
- **Every benefit is a re-runnable calculation** with sourced inputs and a confidence tag. Reviewers check arithmetic; they can't check adjectives.
- **Outputs are ranges; the case says which end is likelier.** False precision fails the doc even when the direction is right.
- **All three cost layers appear per option** — build, run, opportunity — with the displaced work named, not waved at.
- **The flip-assumption is identified** and, where confidence on it is low, a de-risking step is proposed before full commitment.
- **The recommendation is singular and the runner-up's best argument is stated fairly.** A case that strawmans the alternative converts no skeptics.
- **The ask is the first thing read** — option, cost, benefit range, deadline, in under 40 words.

## When to use this skill

- ✅ "Should we build this?" / "write the business case for X"
- ✅ Build vs buy vs defer with real money or quarters at stake
- ✅ Budget/headcount approval needs a document, not a hallway pitch
- ✅ A persistent "we should really fix this" needs its cost of inaction priced

## When NOT to use this skill

- ❌ The investment decision is already made — go to `prd-draft`
- ❌ Choosing between technologies for an approved initiative — `tech-comparison-matrix`
- ❌ Compressing an existing case for execs — `exec-summary`
- ❌ Trivial cost ("should we buy a $400/yr tool") — the case costs more than the decision; just decide

## Anti-patterns to avoid

- ❌ **Omitting do-nothing.** Every option looks good against an unexamined status quo — that's why it gets omitted.
- ❌ **Adjective benefits.** "Improved efficiency, better experience, reduced risk" — three claims, zero numbers, nothing a reviewer can challenge.
- ❌ **False precision.** "327% ROI" from three guesses. Ranges with a stated lean, always.
- ❌ **Year-one costing.** Build cost without run cost — the buy option's renewal pricing and the build option's maintenance both live in year 2+, which is where cases go to die.
- ❌ **Sunk-cost scaffolding.** "We've already invested 2 quarters" argues for nothing; the case is forward-looking from today's zero.
- ❌ **Option theater.** Two deliberately weak alternatives flanking the favorite. Reviewers notice, and the case loses its credibility along with the vote.
- ❌ **Burying the ask.** Page 4, paragraph 2, "in light of the above we suggest…" — the sponsor read the first five lines; the ask lives there or nowhere.

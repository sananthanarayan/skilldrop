---
name: strategy-analysis
description: Run a strategy framework — SWOT/TOWS, Porter's Five Forces, or PESTLE — on a product, company, or market question, choosing the right framework for the question and forcing every cell to carry evidence and a so-what. Use when the user asks for a SWOT, a competitive/market analysis, "should we enter this market", "what's our position against X", or a macro-environment scan.
---

# strategy-analysis

Runs the classic strategy frameworks the way a good strategist does and a bad deck doesn't: the framework is chosen to fit the question, every cell carries evidence and an implication, and the output ends in ranked, committal so-whats — not a filled-in grid. The grid is the working, never the deliverable. Sibling of `tech-comparison-matrix` (tech selection between named options) and `business-case` (a costed invest/defer decision); this skill is for the strategic question *before* options are named.

## How to respond

1. **Classify the question, then pick ONE framework** (two only when the question genuinely spans both, and say why):

   | The question is about… | Framework |
   |---|---|
   | Our position: what to exploit, fix, or defend, feeding a near-term decision | **SWOT → TOWS** (SWOT alone is banned — see step 3) |
   | Industry attractiveness / profit pressure: "should we enter", "why are margins thin", "can we defend" | **Porter's Five Forces** |
   | Macro environment: regulation, technology shifts, demographics affecting a multi-year bet | **PESTLE** |

   The user asked for a framework by name and it fits → run it. It doesn't fit → say so in one line and run the fitting framework instead — the quality bar treats a misfit framework as a category error, and a "SWOT" request that's really "should we enter this market" is Five Forces work; run the requested framework only if the user insists after the flag. Portfolio-allocation questions across many products (BCG-matrix territory) → name it, note it needs per-product market-share and growth data, and run it only if that data is supplied.

2. **Collect the evidence base before filling anything.** Name what is known `[data: …]`, reported `[reported by …]`, drawn from general market knowledge `[market: …]`, and assumed `[assumption]`. The `[market: …]` tag exists because on a short prompt most cells are filled from the model's own market knowledge — that's legitimate, but it must stay distinguishable from the user's facts and from guesses. Ask at most 2 questions, spent on the decision the analysis feeds ("what decision does this inform, and by when?") and the competitive set ("who do customers actually compare you to?"). No decision named → the analysis has no ranking criterion; get one before proceeding. Non-interactive run (no user to ask): derive the most plausible decision from the input, state it as `[assumption]` at the top, and rank against it; none derivable → emit `BLOCKED: need the decision this analysis feeds` rather than an unranked survey.

3. **Fill the framework with cells that pass the three tests.** Every entry must be (a) **specific** — a competitor, number, or named capability, not a category; (b) **evidenced** — carrying one of the step-2 tags; (c) **consequential** — with a one-line "so:" implication. ✅ *"S: 4,000 paying tenants' workflow data no rival can train on `[data: billing]` — so: the switching cost is the moat to invest in"* — ❌ *"S: strong team"*. Framework-specific rules:
   - **SWOT** never ships alone — cross it into **TOWS** actions: S×O (attack), S×T (defend), W×O (fix to unlock), W×T (the exposed flank, named honestly). The TOWS quadrants are the output; the SWOT grid is scaffolding.
   - **Five Forces**: each force gets a pressure rating (🟥 high / 🟧 medium / 🟨 low) *with the mechanism* — who holds the power and why (concentration, switching costs, differentiation, substitutes' price-performance). Rate all five; "N/A" is not a rating. Complements/platforms noted where they change the picture.
   - **PESTLE**: only factors that plausibly move *this* decision within its time horizon, each with direction, timeframe, and the exposed asset. Six sections of filler is the classic failure — 3 sharp factors beat 18 generic ones; empty letters say "no material factor identified".

4. **Rank the implications and commit.** End with **Implications, ranked** — 3–5 entries ordered by impact on the named decision, each an action-shaped sentence with an owner-shaped subject: ✅ *"Price the enterprise tier before Q3: supplier power is rising (🟥) and the S×O attack window closes when the incumbent's contract cycle renews"*. Then a one-paragraph **verdict** answering the user's actual question, taking a side, and naming what evidence would change it.

5. **Emit in one message**: evidence base (tag summary), the framework grid(s), ranked implications, verdict. Flag every `[assumption]` that appears in a top-3 implication — those are the validation targets. Hand off: options now named and comparable → `tech-comparison-matrix`; investment decision to cost → `business-case`; product direction to test → `prfaq`.

## Quality bar

- **The framework fits the question**, and the doc says why in one line. A SWOT that should have been Five Forces is a category error, not a style choice.
- **Every cell passes specific/evidenced/consequential.** One untagged, implication-free cell is a defect; a grid of them is a horoscope.
- **SWOT always arrives as TOWS.** Four lists with no crossings is inventory, not strategy.
- **Every Five Forces rating names the mechanism.** "Rivalry: high" without who/why is a vibe with a color.
- **The implications are ranked and action-shaped**, tied to the named decision — not "consider monitoring the competitive landscape".
- **The verdict takes a side** and names what would change it. An analysis that ends "it depends" has refused its job.

## When to use this skill

- ✅ "Run a SWOT on our developer-tools product" (arrives as SWOT→TOWS)
- ✅ "Should we enter the SMB payroll market?" / "why are margins compressing?"
- ✅ "What macro trends threaten this 3-year platform bet?"
- ✅ A strategy offsite needs a rigorous pre-read instead of a brainstorm

## When NOT to use this skill

- ❌ Choosing between named technologies or vendors — `tech-comparison-matrix`
- ❌ A costed build/buy/defer decision — `business-case`
- ❌ Testing a specific product concept — `prfaq`
- ❌ Quarterly goal-setting — `okr-cascade`

## Anti-patterns to avoid

- ❌ **Framework theater.** Running all three frameworks "for completeness" — each unfits the others' question, and the reader drowns. One question, one framework, one verdict.
- ❌ **Horoscope cells.** "Strength: experienced team. Weakness: limited resources. Opportunity: growing market." True of every company that ever existed, therefore informative about none.
- ❌ **SWOT as the deliverable.** The four quadrants are raw material; the TOWS crossings are where a decision lives. Shipping the grid alone ships the homework, not the answer.
- ❌ **Unranked implications.** Ten equal-weight bullets delegate the actual judgment to the reader — the ranking *is* the analysis.
- ❌ **Threat inflation.** Every macro trend rated critical so nothing is. Severity must be calibrated to the named decision's time horizon and exposed assets.
- ❌ **Evidence-free confidence.** A verdict resting on untagged claims. The tag discipline exists so the reader can see exactly which legs are load-bearing guesses.

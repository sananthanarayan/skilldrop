# Worked example — SWOT arriving as TOWS for a market-entry decision

Input → output oracle for `strategy-analysis`. Shows the framework justified in one
line, evidenced/consequential cells, the mandatory SWOT→TOWS crossings, ranked
action-shaped implications tied to the decision, and a verdict that takes a side.

## Input

> "Should [Acme], a mid-market B2B analytics vendor, enter the SMB self-serve
> segment next year? Decision owner wants a go / no-go with conditions."

## Framework fit (one line)

**SWOT→TOWS**, not Five Forces: the question is about *our* fit to a new segment (internal capabilities vs. external openings), not the structural attractiveness of the industry.

## SWOT (every cell specific · evidenced · consequential)

| | Helpful | Harmful |
|---|---|---|
| **Internal** | **S1** Self-serve onboarding already built for mid-market trials (evidence: 40% of trials activate with zero sales touch) → *marginal cost to serve SMB is low.* | **W1** Pricing starts at $2k/mo (evidence: current floor plan) → *5–10× above SMB willingness-to-pay; no viable entry SKU.* |
| **External** | **O1** No incumbent owns SMB self-serve analytics in this niche (evidence: top 3 competitors are all sales-led, $10k+ ACV) → *an unserved segment with a wedge.* | **T1** Two horizontal BI tools added SMB free tiers this year (evidence: their changelogs) → *the window is closing; a free tier resets price expectations.* |

## TOWS crossings (the strategy — inventory becomes moves)

- **S1 × O1 (invest):** Package the existing zero-touch onboarding as a low-price self-serve SKU to claim the unserved niche before it's contested.
- **W1 × T1 (defend/decide):** The $2k floor collides head-on with free tiers — a new SMB SKU is a *prerequisite*, not an option; without it, don't enter.
- **S1 × T1 (hedge):** Low cost-to-serve means an SMB tier can be near-free to run, so a defensive free/low tier is affordable if a competitor forces it.
- **W1 × O1 (fix-first):** The opportunity is real but unreachable until pricing is solved — so pricing is the gating workstream, not marketing.

## Ranked implications (action-shaped, tied to the go/no-go)

1. **Gate the decision on a validated SMB SKU** (target ≤ $99/mo, positive unit economics at self-serve volume). No SKU → no-go. *(from W1×T1, W1×O1)*
2. **Run a 60-day self-serve pilot** on the existing onboarding to test activation without sales. *(S1×O1)*
3. **Pre-commit a free-tier response** so a competitor's move doesn't catch us flat. *(S1×T1)*

## Verdict (takes a side + what would change it)

**Conditional GO** — enter *only* after a sub-$100 SKU clears a unit-economics test in a 60-day pilot; the low cost-to-serve and the open niche make the upside real, but the pricing gap is disqualifying until fixed. **What flips it to no-go:** the pilot shows self-serve activation < 20% (the zero-touch advantage doesn't transfer), or a horizontal BI tool ships a *vertical* SMB tier first (the wedge closes).

## Why this passes the quality bar

The framework choice is justified; every cell is specific, evidenced, and carries a "→ so what"; SWOT is delivered *as TOWS* with real crossings; implications are ranked and tied to the named decision; and the verdict commits with a falsifiable flip-condition instead of "it depends."

# Worked example — build vs. buy a feature-flag system

Input → output oracle for `business-case`. Shows the ask first (< 40 words), Option 0
costed, benefits as re-runnable calculations with confidence tags, all three cost
layers, ranges, the flip-assumption, and a singular recommendation that states the
runner-up's best argument fairly.

## Input

> "Should [Acme] build an in-house feature-flag system or buy a SaaS one? ~30
> engineers, currently gating releases with config files and redeploys."

## Output

### The ask
**Buy the SaaS feature-flag service (~$18–30k/yr).** It pays back in < 3 months against ~$140k of first-year build cost and recurring toil, and frees roadmap capacity now. Decision needed before next quarter's release-velocity commitments.

### Options (Option 0 is costed)

| Option | Build (one-time) | Run (yr 1) | Opportunity cost |
|---|--:|--:|--:|
| **0 — Status quo** (config + redeploy) | $0 | ~$60–90k/yr toil | Slow releases → est. 1–2 delayed launches/yr |
| **1 — Build in-house** | ~$110–160k | ~$25–40k/yr (on-call, maint.) | 2 eng × 3–4 mo off roadmap |
| **2 — Buy SaaS** | ~$5k (integrate) | ~$18–30k/yr license | ~1 eng-week integration |

### Benefits (re-runnable calculations, sourced, confidence-tagged)

- **Toil removed vs. Option 0:** each gated release currently costs ~1 eng-hr of redeploy coordination × ~15 releases/mo × $120 loaded/hr = **~$22k/yr** recovered. *(confidence: medium — release count from deploy logs; hourly is loaded-cost estimate.)*
- **Incident reduction:** flag-based instant rollback vs. redeploy shortens mean remediation from ~40 min to ~5 min; at ~6 rollback-worthy incidents/yr that's ~3.5 hrs × team = **~$8–15k/yr** avoided. *(confidence: low — incident count is small-sample; range reflects it.)*
- **Release velocity:** decoupling deploy from release plausibly removes 1–2 launch slips/yr; value is real but **not costed here** (depends on launch revenue) — flagged for the decision owner.

Totals are ranges; the **lower end is likelier** for the hard-dollar items (toil is the solid number; incident/velocity are directional).

### The flip-assumption
The case flips to **Build** only if **flag evaluation must run in a data plane the SaaS can't reach** (e.g. strict data-residency or sub-ms in-process evaluation at scale). Confidence that this *doesn't* apply is medium. **De-risking step before committing to Buy:** a 1-week spike confirming the SaaS SDK meets latency + residency requirements — cheap insurance against the one assumption that would reverse the decision.

### Recommendation
**Buy (Option 2).** Lowest first-year cost, fastest payback, and it returns ~2 engineers to the roadmap that Build would consume. **The runner-up's best argument, stated fairly:** Build is genuinely better *if* flag evaluation becomes a core differentiator or a hard data-residency constraint emerges — in that world the SaaS boundary bites and owning the system is worth the cost. The spike above is what tells us which world we're in.

## Why this passes the quality bar

The ask leads in under 40 words; Option 0 is present and costed; every benefit is a calculation with sourced inputs and a confidence tag; outputs are ranges naming the likelier end; all three cost layers appear per option; the flip-assumption is identified with a de-risking step; and the recommendation is singular while stating the runner-up's strongest case honestly.

# Rubric: Exec Summary / 1-Pager

Mirrors `exec-summary`'s quality bar. The test: can a VP read this in 60 seconds between meetings and either approve, push back, or ask exactly one clarifying question?

## Blockers
- **The Ask is the first thing.** If "What we need from you" is at the bottom of page 2, the doc is failing its only job.
- **TL;DR is self-contained.** A reader who stops after the TL;DR must be able to decide. No "see below".
- **One page.** ~300–400 words rendered including headings. If it's two pages, it's not an exec summary.
- **Plain language in the first paragraph.** Any unrecognized jargon in the first 100 words blocks comprehension.

## Major
- **Business impact is quantified or explicitly "directional".** Made-up precision is worse than honest qualification.
- **Risks are project-specific.** Generic risks ("scope creep", "team turnover") prove nothing was thought through.
- **What we need from you is concrete.** ❌ *"Alignment"* ✅ *"Sign off on the $1.2M budget by Friday."*
- **Cost & timeline are numbers, not adjectives.** Even rough numbers ("$200–400k, 5–7 months") beat "modest investment, short timeframe."
- **Audience-fit.** A 1-pager for the CFO leads with cost; one for the CTO leads with technical risk; one for the board leads with strategic context. Wrong leading section ⇒ major finding.

## Minor
- **Active voice.** "You'll need to approve…" beats "Approval will be required…".
- **Adjectives stripped.** "Robust", "scalable", "innovative", "leverage" — flag each occurrence as a candidate replacement.
- **History the audience already knows is cut.** "As you know, in 2022 we launched…" is calorie-free.
- **Section ordering follows the template** (Ask → TL;DR → Impact → Cost/Timeline → Risks → Need-from-you). Deviation needs a reason.

## Nits
- Bullet density (4–5 max per section in a 1-pager).
- Numbers formatted consistently ($1.2M vs $1,200,000 — pick one).
- No trailing whitespace / orphan headings.

## Anti-patterns to flag (always major)
- Burying the recommendation on page 2.
- Listing technical wins ("reduced p99 by 40ms") with no business translation.
- Asking the exec to "review the full design doc for details" without specifying which sections.
- "Next steps: align with stakeholders" — empty-calorie ask. Demand the *actual* action.
- Hedging language ("we believe", "in many cases", "potentially") in the recommendation sentence.

## What's working — look for
- A quantified Ask that's calibrated (number + timeframe + currency).
- A project-specific risk with a real mitigation.
- A line that translates a technical metric into a business outcome.
- Audience-appropriate framing (CFO leads with $, board leads with strategy).
- The doc visibly cuts material that would belong in the design doc.

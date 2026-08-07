# Rubric: Tech-Comparison Matrix

Mirrors `tech-comparison-matrix`'s quality bar.

## Blockers
- **The question is one sentence and answerable.** ❌ *"Database options"* ✅ *"Pick a primary OLTP datastore for the new checkout service."*
- **≥2 candidates.** A "comparison" with one candidate is a proposal, not a comparison.
- **Criteria are listed before scoring.** Otherwise the matrix is just opinion in a table.
- **Weights are explicit** (even if equal) — otherwise the recommendation is unaccountable.
- **A recommendation is made.** A matrix that ends with "it depends" without a follow-up framing is unfinished.

## Major
- **Each criterion has a 1-line definition** of what "good" looks like, so scores are comparable.
- **Scores are justified.** A score of 5/5 with no rationale is decoration. Each cell needs at least a one-line why.
- **Constraints / non-negotiables called out** *before* scoring — otherwise low-weighted criteria can mask hard disqualifiers.
- **The recommendation cites which weighted scores carry it,** not "X is the best".
- **Bias acknowledged.** If the team already prefers X, the doc should say so and explain why the matrix didn't just rubber-stamp that preference.

## Minor
- **Workload profile section** — read/write ratio, scale targets, consistency requirements. Without this, criteria like "scalability" are unanchored.
- **Cost dimension** quantified (or marked qualitative if vendor pricing is opaque).
- **Time horizon** stated ("12 months" vs "5 years" changes which scores matter).
- **Operability score considered**, not just feature parity.

## Nits
- Table formatting; column alignment.
- Consistent score scale (1–5 vs 0–10 — pick one).
- Vendor / project names spelled correctly and consistently.

## Anti-patterns to flag (always major)
- Cherry-picked criteria that obviously favour one candidate (e.g. listing 5 features that only Vendor A has).
- Mixing weights and scores into one number (multiplied) without showing both — strips reviewers of the ability to disagree on weighting.
- Footnotes that quietly override the matrix's conclusion ("we picked X anyway because…") — that's a real reason, surface it.
- Score for "community / ecosystem" without any concrete metric (GitHub stars, Stack Overflow questions, vendor revenue).

## What's working — look for
- A non-winner scoring high on a single load-bearing criterion — that's honesty.
- Weights that visibly shifted the outcome (small change in weighting changes the recommendation — and the doc says so).
- A "what would change our mind" section.
- Explicit acknowledgement that the team's existing skill profile influenced one criterion.

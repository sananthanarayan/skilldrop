# source-synthesis — reference

## Citation format

One bracket per claim, one or more parts separated by `;`. Each part is a source id, a colon,
and a location.

| Source type | Location | Example |
|---|---|---|
| Paginated document | page or page range | `[S1:p4]`, `[S1:pp4-6]` |
| Document with numbered sections | section | `[S2:§3.2]` |
| Report with figures or tables | table or figure | `[S3:Table 2]` |
| Transcript or recording | timestamp | `[S4:00:12:30]` |
| Web page with no pages | heading | `[S5:"Results" section]` |
| Several sources | parts joined by `;` | `[S1:p4; S3:§2.1]` |

Don't write `[S1, S2]`: the checker flags it as malformed, because it can't tell which
location belongs to which source. Use `[outside]` for anything that doesn't come from the
supplied sources.

The sources list sits under a `## Sources` heading, one per line, starting with the id:

```
## Sources

- S1: Northwind People Team, "Four-day week pilot: final report", internal report, Jun 2026, 18 pp.
- S2: Interview transcript, Acme support team lead, 12 Mar 2026, 41 min.
```

## Evidence strength

Rate each finding on what supports it, not on how plausible it sounds. Use the criteria below
and name the ones that decided the rating.

| Criterion | Stronger | Weaker |
|---|---|---|
| Independent sources | Several sources with separate data | One source, or several repeating one dataset |
| Source type | Primary data: study, dataset, controlled pilot, transcript | Commentary, opinion, news report of someone else's work |
| Method | Comparison group, before-and-after with a baseline, stated sample | Anecdote, self-report with no baseline, method not stated |
| Sample size | Large enough for the claim, and stated | Small or not stated |
| Recency | Current for the question | Old enough that conditions have changed |
| Directness | Measures the thing asked about | Measures a proxy or a different population |
| Agreement | Sources agree | Sources conflict without an explanation |

Ratings:

- **Strong:** two or more independent primary sources with sound methods agree, and none
  credibly disagrees.
- **Moderate:** one sound primary source, or several weaker sources that agree.
- **Limited:** one weak source, self-report only, a proxy measure, or commentary only.
- **Conflicting:** credible sources disagree and the sources don't explain why.

For health and clinical questions, fields use formal systems such as GRADE to rate certainty
of evidence. If the user works in such a field, ask whether they need that system instead of
the simple scale here.

## Handling disagreement

1. Check whether the sources measure the same thing: same definition, population, period and
   unit. Many "disagreements" are different questions.
2. If they do, look for a difference in method or sample that would explain the split, and
   name it if a source states it.
3. If nothing explains it, rate the finding **conflicting** and report both sides with their
   citations. Don't pick the side you find more plausible without saying why.

## Independence

Count sources by line of evidence, not by document:

- A news article reporting a survey is the survey, not a second source.
- Two reports by the same team on the same data are one line of evidence.
- Interviews with people in the same team can share one view; say so if the transcripts show it.

Note dependencies in the source register: "S4 reports S1's survey; counted with S1."

## Common distortions

- **Hedge loss:** "may", "in this sample", "associated with" dropped in the summary.
- **Scope creep:** a finding about one company or country stated as a general truth.
- **Selective citing:** quoting the part of a source that agrees and skipping its caveats or
  limitations section.
- **Number drift:** rounding or converting a figure (relative to absolute, monthly to yearly)
  without saying so.
- **Outside leakage:** adding a well-known figure from memory because it "fits". Tag it
  `[outside]` or leave it out.

## What "what the sources do not say" means

Gaps are questions the user cares about that the sources don't answer. "What the sources do
not say" also covers inferences a reader is likely to draw that the sources don't support.
✅ *"The pilot reports output held steady; it doesn't say whether customers noticed slower
replies."* This section stops the synthesis from being read as more than it is.

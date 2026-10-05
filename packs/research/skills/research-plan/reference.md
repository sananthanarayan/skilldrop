# research-plan — reference

## Choosing a method

Pick the cheapest method that can answer the sub-question to the confidence the decision needs.

| Method | Use when the sub-question is | Typical scope | Watch out for |
|---|---|---|---|
| **Data pull** | "How much / how often / what changed" and you already have the data | A query over existing records, one to three days | Definitions that changed over time; data that measures a proxy |
| **Desk research** | "What do others know": published studies, statistics, competitor material | 10–30 sources screened, 5–12 kept | Publication bias, vendor marketing, old data |
| **Interviews** | "Why / how / what's it like" from people with direct experience | 5–12 people per group | Leading questions, only talking to fans, small samples read as statistics |
| **Survey** | "How common is this view" across a group too large to interview | Enough responses for the split you need | Low response rates, self-report bias, questions that suggest the answer |
| **Experiment or pilot** | "Does X cause Y here", and the decision is costly to reverse | A test group and a comparison group, a fixed period | Too short to show the effect; no baseline |

Rules of thumb:

- Existing data before new data. A data pull before a survey.
- Interviews explain; they don't measure. Never report "7 of 10 interviewees" as a percentage
  of a population.
- Run an experiment only when the decision justifies the time, and say up front what result
  counts as success.

## Inclusion and exclusion criteria

Write them before searching so the source list can't drift towards the answer you want.

| Dimension | Example inclusion | Example exclusion |
|---|---|---|
| Date | Published 2019 onwards | Before 2019, unless it's the original study others cite |
| Geography | UK, EU, North America | Regions with different labour law, if that matters to the decision |
| Population | Knowledge workers, support or service roles | Manufacturing, shift work |
| Source type | Primary studies, pilot reports, official statistics, surveys with stated methods | Opinion pieces, vendor marketing, press releases with no data |
| Method | Before-and-after with a baseline, or a comparison group | Self-report only, with no baseline |
| Language | English | Others, unless translation is available |

Record why each excluded source was excluded, in one word, so the user can see the screen
was fair.

## Search strings

Group synonyms with `OR` inside brackets, join concepts with `AND`, and quote phrases.

```
("four-day week" OR "4-day week" OR "compressed workweek" OR "reduced hours")
AND (productivity OR output OR "response time")
AND (pilot OR trial OR study)
```

Engine notes. Check the engine's own help page before relying on an operator; these are the
common, documented ones:

- **Google and Google Scholar:** quotes for phrases, `OR` in capitals, `-` to exclude a word,
  `site:` to restrict to a domain (Google web search). Scholar has a date-range filter in
  the left sidebar.
- **Academic databases** (for example, library databases a university or company subscribes
  to): most support `AND`, `OR`, `NOT`, brackets and quotes, and many support `*` as a
  truncation wildcard. Field tags differ by database.
- **Internal wikis and drives:** usually keyword only. Run each synonym as its own search.

Always add one search for the opposite of what the user expects:

```
("four-day week" OR "compressed workweek") AND (failed OR abandoned OR reversed OR "customer complaints")
```

## Stopping rules

Set both kinds. Stop at whichever comes first.

- **Sufficiency (saturation):** each sub-question has an answer at the confidence the decision
  needs, or the last three sources or interviews added nothing new to it.
- **Budget:** a cap in hours or a date. When the cap comes first, deliver what you have and
  list the open sub-questions with what it would take to close each.

Confidence the decision needs depends on how costly and reversible it is. A reversible,
cheap decision needs a direction, not proof. A costly, one-way decision needs the strongest
evidence available, and may justify a pilot.

## Planning failures

- **The question changes mid-way** and nobody notices. Re-read the plan's question at each
  check-in; if it changed, change the plan on purpose.
- **Sub-questions nobody needs.** Test each one: "if the answer is X, what do we do
  differently?" No change, cut it.
- **Thresholds written after the findings.** Write them first.
- **Access assumed.** Confirm early that the data, people and paywalled sources are reachable.
- **One method for everything.** Usually the right plan mixes a data pull, some desk research
  and a few interviews.

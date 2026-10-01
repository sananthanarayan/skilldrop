---
name: research-plan
description: Turn a vague research question into a research plan — the decision the research serves, the precise question and sub-questions, what finding would change the decision, a method per sub-question (desk research, interviews, data pull, experiment), source types with inclusion and exclusion criteria, ready-to-run search strings, a stopping rule for when you have enough, and the deliverable. Starts by asking what decision the research is for. Use when the user says "I need to research X", "help me scope this research", "how should I investigate…", "what should I look into before deciding…", or wants a research or discovery plan.
---

# research-plan

You turn "can you look into X?" into a plan that someone can run and finish. Research without
a decision attached never ends, so the plan starts from the decision and works back: what
would have to be true to choose A over B, which sub-questions test that, how to answer each
one, and when to stop. The output is a one-to-two page plan, not the research itself.

The plan feeds two siblings: `source-synthesis` turns the sources you collect into cited
findings, and `hypothesis-comparison` ranks rival explanations when the question is "why did
this happen?". If interviews are one of the methods, `requirements-interview` writes the
question scripts for stakeholder interviews.

## How to respond

1. **Ask about the decision first, in one message.** Ask: *"What decision will this research
   inform, who makes it, and by when?"* Add one more question only if needed: what the user
   already believes the answer is. That's at most two questions. Research without a decision
   is the main failure this skill prevents, so don't skip this step even if the topic is
   clear. ✅ *"Whether to move support to a four-day week from January; the COO decides on
   1 Nov."* ❌ *"Understand four-day weeks."*

2. **Write the precise question.** One sentence that names the population, the thing being
   tested, the comparison and the timeframe. ✅ *"For a 14-person B2B support team, does a
   four-day week keep first-response time within 10% of today over six months?"* ❌ *"Do
   four-day weeks work?"* If the user's question can't be answered in the time they have,
   narrow it and say what you cut.

3. **Break it into three to six sub-questions.** Each one must be answerable on its own and
   matter to the decision. Drop any sub-question whose answer wouldn't change what the user
   does, however interesting it is.

4. **Say what would change the decision.** For each sub-question, write the finding that would
   push the decision one way or the other, with a threshold where one makes sense: *"If
   response times rise more than 10% in comparable pilots, don't move without a staggered
   rota."* Write these before any research starts, so the findings can't be read to fit.
   Note the user's current belief and what evidence would overturn it.

5. **Pick a method per sub-question.** Choose the cheapest method that can answer it, from
   desk research, interviews, a data pull, a survey, or an experiment (the guide is in
   [`reference.md`](reference.md)). For each, give the sample or scope, who does it, and
   the time it takes. Prefer existing data over new data, and a data pull over a survey.

6. **Define the sources.** For desk research, list the source types to use in order of
   weight (primary studies, official statistics, industry surveys, practitioner write-ups,
   news) and write **inclusion and exclusion criteria**: date range, geography, population,
   language, study type, and minimum method standard. ✅ *"Include: pilots or studies from
   2019 on, in knowledge-work or support roles, with a before-and-after measure. Exclude:
   opinion pieces, vendor marketing, manufacturing shifts."*

7. **Write the search strings.** Give strings the user can paste, with synonyms grouped in
   `OR` and concepts joined with `AND`, plus where to run each (Google Scholar, a named
   database, company filings, internal wiki). Note the date filter. Search syntax differs by
   engine; the notes are in [`reference.md`](reference.md).

8. **Set the stopping rule.** Say when the research is done, before it starts. Combine a
   **sufficiency** test (each sub-question answered to the confidence the decision needs, or
   new sources stop changing the answer: "three sources in a row add nothing new") with a
   **budget** cap (hours or a date). When the cap comes first, the deliverable says which
   sub-questions are still open.

9. **Name the deliverable.** State the format, the audience, and the date: for example, a
   two-page synthesis with cited findings and a recommendation, made with `source-synthesis`.
   List the risks to the plan (no access to data, biased sources, too few interviewees) with
   a fallback for each.

10. **Write it up with [`templates/research-plan.md`](templates/research-plan.md).** Keep it
    to two pages. A plan longer than that tends to get made instead of the research.

**Non-interactive runs** (subagent, CI, headless): if the decision can't be inferred from the
input, emit `BLOCKED: need the decision this research informs, who makes it, and by when`.
If it can be inferred, state it as `[assumption] Decision: …` at the top. Missing deadlines and
budgets become tagged assumptions (default: two weeks, 15 hours).

## Useful references in this skill

- [`reference.md`](reference.md) — choosing a method, inclusion and exclusion criteria, search-string syntax by engine, stopping rules, and planning failures
- [`templates/research-plan.md`](templates/research-plan.md) — the plan skeleton
- [`examples/four-day-week-plan.md`](examples/four-day-week-plan.md) — worked example: a vague request becomes a decision-led plan

## Quality bar

- **The plan names the decision, who makes it, and the date.** Every sub-question traces back to it.
- **The question is precise:** population, intervention or topic, comparison, timeframe.
- **Each sub-question has a "would change the decision" finding,** written before research starts, with a threshold where one makes sense.
- **Each sub-question has a method, a scope, an owner and a time,** and the method is the cheapest one that can answer it.
- **Inclusion and exclusion criteria are explicit** for desk research: dates, geography, population, source type.
- **Search strings are ready to paste,** with synonyms and where to run them.
- **There is a stopping rule** with both a sufficiency test and a budget cap.
- **Nothing in the plan states findings.** It doesn't present a guess at the answer as known.

## When to use this skill

- ✅ "I need to research X before we decide Y"
- ✅ Scoping desk research, a literature review or a discovery sprint
- ✅ A question that keeps growing and needs a boundary and an end date
- ✅ Choosing between interviews, data, surveys and experiments for a question

## When NOT to use this skill

- ❌ The sources are already collected and need summarising — `source-synthesis`
- ❌ Ranking rival explanations for something that already happened — `hypothesis-comparison`
- ❌ Writing the interview scripts for stakeholders — `requirements-interview`
- ❌ A strategy framework such as SWOT or Five Forces on a market — `strategy-analysis`
- ❌ Comparing named technologies or vendors — `tech-comparison-matrix`
- ❌ Turning a messy thread into a brief for another skill — `brief-intake`

## Anti-patterns to avoid

- ❌ **Research with no decision.** "Learn about four-day weeks" has no end and no use.
- ❌ **A dozen sub-questions.** Six is the most a person can work through; cut the ones that wouldn't change the decision.
- ❌ **Writing the thresholds after the findings.** Then any result can be read as support.
- ❌ **A survey by default.** Check whether the answer already sits in data you have.
- ❌ **"Search Google for four-day week".** Give the string, the synonyms, the engine and the date filter.
- ❌ **No stopping rule.** The research ends when the budget runs out, with nothing written.
- ❌ **Only sources that agree with the user's belief.** Include a search for the opposite.
- ❌ **Showing the machinery.** The reply and the artifact are for the person who asked. Don't mention this skill, its files, templates, caps or internal terms, or that the run is non-interactive. Name another skill once, at the end, as a suggested next step, never inside the artifact.
- ❌ **A bare `BLOCKED` line.** Keep the `BLOCKED: need <X>` line, then write for a person: what is missing in plain words, what you will produce once you have it, and anything the request already lets you say.

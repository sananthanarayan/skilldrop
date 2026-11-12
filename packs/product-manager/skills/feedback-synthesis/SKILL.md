---
name: feedback-synthesis
description: Turn raw customer feedback — interview notes, support tickets, NPS or CSAT verbatims, app-store reviews, sales-call notes — into ranked themes a product decision can rest on, each a problem statement rather than a feature request, counted by distinct people or accounts not mentions, with segments, severity kept separate from frequency, verbatim quotes with source IDs, what people value, where sources disagree, what the sample cannot tell, and the questions for the next interviews. A stdlib script computes the counts. Use when the user says "what are customers telling us", "synthesise this feedback", "find the themes in these tickets / reviews / NPS comments", "affinity map these interview notes", or "what should we fix first based on feedback".
---

# feedback-synthesis

Feedback arrives as a pile of tickets, survey comments, reviews and notes, and the loudest
thing in the pile is rarely the most important. This skill turns the pile into a short list of
problems worth acting on, with numbers that are counted rather than guessed and quotes that can
be traced to the item they came from. It feeds discovery: the themes go to `brief-intake` to
become a brief, and the open questions go into the next round of interviews.

## How to respond

**Five rules come before the steps and outrank them:**

- **Answer what was asked, first.** Open with what to act on and why, in plain words. If the
  data contradicts the user's premise ("the CSV export is our biggest problem"), say so in the
  opening lines, with the count that shows it.
- **Count people, not mentions.** One customer filing six tickets is one customer. Every number
  in the reply is a count of distinct people or accounts, computed, and says which.
- **Use only what the input contains.** No quote, count, segment, customer name, revenue figure
  or reason that isn't in the feedback. What is missing goes in **What this can't tell us** and
  the interview questions, never into a theme.
- **Deliver from what there is.** Feedback without IDs, segments or a stated decision still gets
  a synthesis, with the limit named once. Ask first only when there is no feedback at all.
- **Write for someone who has never heard of this skill.** No skill names, file paths, script
  output, theme codes or "S2" shorthand without its meaning. A next step is one plain sentence
  at the end.

1. **Read every item before coding any.** List the sources and, for each, what an item is
   (a ticket, a response, an interview, a review), what identifies the person (account ID,
   respondent ID, reviewer name, nothing), and what segment fields exist (plan, role, region,
   tenure, company size, score). Decide the counting unit: **accounts** for B2B feedback where
   account IDs exist (two staff from one customer are one account), **people** otherwise.
   Match people across sources only on a shared ID: an interviewee whose account ID appears in
   the tickets is the same account. Anonymous rows are never merged by guesswork. A rep's or
   interviewer's guess about what someone needs ("they'll probably need SSO") is not that
   person's feedback: leave it uncoded and say so if it matters to the answer.

2. **Write the codebook as problem statements.** 4–12 themes, each one sentence saying who hits
   what and what it costs them, plus a short code. A theme must be something the next interview
   could prove wrong.
   - ✅ *"Clients in the EU can't complete card payments; the error says authentication failed
     and payment arrives weeks later by transfer."*
   - ❌ *"Payment issues"* / *"Users want a better experience"* / *"Improve usability"* — banned:
     nothing could disprove them.
   - **A feature request is evidence of a need, not the need.** Rewrite it into the job behind
     it and keep the request as a quote. ✅ *"Changing a rate means editing every recurring
     invoice by hand — 30 to 58 invoices per price change"*, with "Please add bulk edit"
     quoted as evidence. ❌ Theme title *"Bulk edit"*. Never let the loudest proposed solution
     become the title.
   - **A request with no stated reason is not a theme.** Three "add dark mode" comments with no
     context go under **Requests with no stated need**, and the reason becomes an interview
     question. Don't invent the need.
   - Code what people value as themes too, prefixed `+` (`+reminders`). These become **What
     not to break**.

3. **Rate severity per item, separately from frequency.** From what happened to the person, not
   how angry they sound; capitals and exclamation marks don't raise it.

   | Level | Meaning | Example |
   |---|---|---|
   | **S1 — blocker** | A core job can't be done, or money, data, security or compliance is at stake | Clients can't pay; data lost; can't log in |
   | **S2 — major** | Done only through a costly recurring workaround, or the person says they'll leave over it | Reformatting an export by hand every month |
   | **S3 — minor** | Slower or annoying; the workaround is quick | An extra click to find a report |
   | **S4 — cosmetic** | Looks, wording, preference, no stated cost | Blurry logo on a PDF |

   More rules and edge cases in [`reference.md`](reference.md).

4. **Fill the coding sheet and run the counts.** One row per item in the shape of
   [`templates/coding-sheet.csv`](templates/coding-sheet.csv): `item_id`, `person_id` (blank
   when the source has none), `source`, the segment columns, `themes` separated by `;` (a code
   may carry its own severity as `code:S1`), and `severity`. When a raw segment is too fine to
   show a pattern, add a derived column beside it (country → `market` EU / UK / US; employee
   count → `size` band). Then run:

   ```bash
   # Claude Code
   python3 "${CLAUDE_SKILL_DIR}/scripts/theme_counts.py" coded.csv --person-label account -o counts.md
   # Other IDEs (from the skill folder)
   python3 scripts/theme_counts.py coded.csv --person-label account -o counts.md
   ```

   It prints per theme the distinct people with an ID, the items with no ID (beside the count,
   never added to it), mentions, repeat filers, sources, the segment breakdown with a flag when
   a theme sits in one segment only, the ranking severity, and the items with no theme. If no script can run, count by hand from the sheet and show the
   tally per theme. Above about 300 items, code the most recent full period or a stated sample,
   and say the counts cover that sample.

5. **Read the counts, then fix the codebook.** Re-read the unthemed items: three or more about
   the same thing is a missing theme. Where one person drives most of a theme's mentions, the
   theme is ranked on its people count. Where a theme lives in one segment, that is a finding
   (✅ *"Only EU accounts: DE, FR, NL"*), not a footnote. Rerun after any recode.

6. **Rank: severity first, then distinct people.** A theme's severity is the worst level at
   least two people reached; a theme raised by one person takes that person's level and is
   labelled *one report — confirm before acting*. The script's ranking severity column applies
   this rule. A rare issue that stops payment outranks a common cosmetic gripe: say so in those
   words when the ranking differs from the volume order.

7. **Write the reply in the shape of [`templates/synthesis.md`](templates/synthesis.md)**,
   sized to the ask (a few bullets when asked for bullets):
   - **Headline** — what to act on first and why, correcting the premise if needed.
   - **Themes, ranked** — problem statement; distinct people or accounts, plus mentions when
     they differ; segments; severity in words; sources.
   - **Evidence per theme** — 1–3 verbatim quotes, each followed by its source ID:
     *"Took most of a Friday." (I-2)*. The quote is an exact substring of the item; cut with
     "…", never reword, never stitch two items into one quote. An interviewer's or rep's summary
     is reported without quotation marks and attributed to them. The requests behind the theme
     are quoted here too.
   - **What not to break** — what people value, with counts and quotes.
   - **Where the sources disagree** — ✅ *"Interviewees call reminders the reason they stay;
     four accounts report reminders going to a former contact."* Both sides, counted.
   - **What this can't tell us** — each source's sampling bias in one line, and the
     conclusions it rules out. No percentage of the user base from a self-selected sample:
     ✅ *"7 of the 29 accounts that raised a ticket"* — ❌ *"24% of customers"*. Anonymous rows
     that may overlap with identified ones are reported beside the count, never added to it:
     ✅ *"3 accounts, plus one anonymous NPS comment that may be one of them"*.
   - **Questions for the next interviews** — 3–6, each tied to a theme, open, non-leading, and
     at least one that could disconfirm the top theme. ✅ *"Walk me through the last time a
     client couldn't pay you. What happened next?"* — ❌ *"Would a fix for card payments help?"*

8. **Keep the machinery out of the reply.** Theme codes, the coding sheet and the script's report
   are working files; save them only when the user asked. The reply carries the answer.

**Non-interactive runs** (subagent, CI, headless): with no feedback items at all, emit
`BLOCKED: need the feedback itself (tickets, survey verbatims, interview notes or reviews)`,
because a synthesis of what customers "usually say" is fabrication. A missing decision or
audience becomes an `[assumption]` stated at the top (default: *"feeds next quarter's
prioritisation"*). Missing person IDs or segment fields are not blockers: proceed, and state
that the counts are mentions or unsegmented.

## Useful references in this skill

- [`reference.md`](reference.md) — the severity scale with edge cases, sampling bias by source, rewriting requests into problems, codebook rules, counting across sources
- [`templates/coding-sheet.csv`](templates/coding-sheet.csv) — the CSV the script reads
- [`templates/synthesis.md`](templates/synthesis.md) — the reply skeleton
- [`scripts/theme_counts.py`](scripts/theme_counts.py) — distinct-person counts per theme, segments, severity, unthemed items (stdlib, Python 3.9+)
- [`examples/booking-app-feedback.md`](examples/booking-app-feedback.md) — worked example: 16 items from three sources, the coding sheet, the real script output, and the finished reply

## Quality bar

- **Every count is distinct people or accounts,** computed from the coded items, and says which unit; mentions appear only beside it.
- **The ranking puts severity before frequency** and says so where the two disagree.
- **Every theme title is a falsifiable problem statement** naming who and what it costs; no theme is titled with a proposed feature.
- **Every quote is verbatim with a source ID;** paraphrase never sits inside quotation marks.
- **Segments are reported per theme,** and a one-segment theme is called out.
- **Each source's sampling bias is named,** and no percentage of the whole user base is drawn from a self-selected sample.
- **What people value and where the sources disagree** are both present.
- **Interview questions are tied to themes,** open, and include one that could disconfirm the top theme.
- **Nothing is invented:** no quote, count, segment, reason or customer that isn't in the input.

## When to use this skill

- ✅ A pile of support tickets, NPS or CSAT comments, reviews or interview notes, and the question "what are customers telling us?"
- ✅ Checking a stakeholder's claim ("everyone asks for SSO") against the feedback before it goes into a brief
- ✅ Affinity-mapping interview notes after a discovery round
- ✅ Choosing what to fix first from a quarter's feedback

## When NOT to use this skill

- ❌ Planning or running the interviews themselves, or writing the question guide — `requirements-interview`
- ❌ Mapping the stages of a journey a customer goes through — `user-journey-map`
- ❌ Answering a research question from papers, reports or articles — `source-synthesis`
- ❌ Ranking rival explanations for a metric change ("why did churn rise in March?") — `hypothesis-comparison`
- ❌ Turning agreed findings into a brief for a PRD or design doc — `brief-intake`
- ❌ Cleaning up a tracker backlog: duplicates, stale tickets, ordering — `backlog-triage`

## Anti-patterns to avoid

- ❌ **Counting tickets as customers.** "CSV export: 7 tickets, our biggest issue" when six came from one account.
- ❌ **Ranking by volume alone.** Seven blurry-logo complaints above three accounts whose clients can't pay.
- ❌ **The feature as the theme.** "Users want bulk edit" — the theme is the hours lost re-pricing recurring invoices.
- ❌ **Inventing the need behind a bare request.** "Users want dark mode for eye strain" when nobody said why.
- ❌ **Quotation marks around a summary.** A rep's note or the agent's paraphrase presented as the customer's words.
- ❌ **Percentages of the base from a self-selected sample.** "40% of users want an Apple Watch app" from fifteen reviews.
- ❌ **Merging anonymous rows into identified counts** by guessing who wrote them.
- ❌ **Only problems.** Leaving out what people value invites the fix that breaks it.
- ❌ **Vague themes.** "Pricing concerns", "usability", "better experience": name who, what happened, and what it cost.
- ❌ **Leading interview questions.** "Would you use bulk edit?" confirms nothing.

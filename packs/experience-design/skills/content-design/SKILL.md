---
name: content-design
description: Write a content spec for a page or journey from user needs — user-need statements ("As a… I need… so that…"), the questions the page must answer in priority order, the page structure, a plain-language rewrite at a target reading level with a before/after readability check, and an explicit list of what to cut and why. Use when the user wants a content spec, content design, "rewrite this page in plain English", "what should this page say", "our page is too long and nobody reads it", or content for a service or journey.
---

# content-design

Decides what a page or journey should say, starting from what the reader needs to do, not from what the organisation wants to tell them. The output is a content spec: the user needs, the questions in the order readers ask them, the structure that answers them, a plain-language draft, and the cut list. It works at page altitude. `ux-writing` works at string altitude (the button, the error, the empty state); `guide-builder` writes step-by-step how-to guides and reference docs; `information-architecture` decides where the page lives. Content design comes before all three on a new page.

## How to respond

1. **Get the inputs in one message.** Ask at most 2 questions, spent on the weakest of: *who reads this and what they're trying to get done*, and *the source material* (the current page, policy text, notes, support tickets, search terms). Default the target reading level to plain English a 9-year-old could follow for a general audience. For a specialist audience, keep their professional terms but still use short sentences. Default the channel to a web page.

2. **Write user-need statements first.** Format: *As a {specific reader}, I need {to know or do something} so that {their outcome}.* 2–5 needs per page. ✅ *"As a tenant whose boiler has broken, I need to know how fast the landlord must fix it so that I know whether to complain."* — ❌ *"As a user, I need information about repairs."* A need with no "so that" is a topic, not a need. Tag each with its evidence: `[support tickets]`, `[search terms]`, `[research]`, `[assumption]`. If the page serves no user need, say so: that is a finding, and the page may not need to exist.

3. **List the questions the page must answer, in priority order.** Rank by how many readers ask it and how much it blocks them. ✅ *1. Am I eligible? 2. How much does it cost? 3. What do I need? 4. How long will it take?* The order of the questions becomes the order of the page. The organisation's background, history and mission go last or go away.

4. **Structure the page from the questions.** One heading per top question, written as the reader's words (✅ *"How much it costs"* — ❌ *"Fee schedule"*). The answer to the top question sits in the first two sentences under the title. Use lists for 3+ parallel items, numbered steps only for a sequence, and tables for comparisons. If the questions span more than one task, recommend splitting the page and say where the second page goes.

5. **Rewrite in plain language** at the target level. Short sentences (aim for under 20 words, never over 25), common words (*"buy"* not *"purchase"*, *"help"* not *"facilitate"*), active voice with a named actor (*"We will reply within 10 working days"* not *"A response will be issued"*), "you" for the reader, "we" for the organisation. Front-load each paragraph with its point. Keep every fact from the source: plain language changes the words, not the rules. Where a legal term must stay, keep it and explain it once.

6. **Check the before and after** with the readability script and report its numbers as-is:
   ```bash
   # Claude Code
   python3 "${CLAUDE_SKILL_DIR}/scripts/readability.py" before.md
   python3 "${CLAUDE_SKILL_DIR}/scripts/readability.py" after.md --max-sentence 20
   # Other IDEs (from the skill folder)
   python3 scripts/readability.py before.md
   python3 scripts/readability.py after.md --max-sentence 20
   ```
   It reports average sentence length, the share of long words, an estimated Flesch–Kincaid grade and every over-length sentence. The grade is a heuristic: use it to compare the two versions, and fix the flagged sentences. Never quote it as a certified score. If scripts can't run, report sentence counts by hand and say the grade wasn't computed.

7. **Write the cut list.** Every sentence or section removed from the source goes in a table: what was cut, why (*not a user need*, *duplicates page X*, *organisational message*, *out of date*, *belongs on another page*), and where it went if it moved. Nothing disappears silently. Facts that must stay for legal or policy reasons stay, and the reason is noted.

8. **Emit with [`templates/content-spec.md`](templates/content-spec.md)** in one message: reader and target level, user needs, prioritised questions, structure, the plain-language draft, the readability before/after, the cut list, and open questions (facts the source didn't give, policies to confirm). Hand-offs: strings inside a form or flow on the page → `ux-writing`; where the page sits in the site → `information-architecture`; a step-by-step setup or how-to guide → `guide-builder`; the wider journey the page sits in → `user-journey-map`. See [`examples/parking-permit-page.md`](examples/parking-permit-page.md).

**Non-interactive runs** (subagent, CI, headless): a missing reader becomes an `[assumption]` line at the top, derived from the source. Missing source material for a rewrite emits `BLOCKED: need the current page or the facts it must contain`. Never draft a page's facts (prices, deadlines, eligibility rules) from nothing.

## Useful references in this skill

- [`templates/content-spec.md`](templates/content-spec.md) — the content spec skeleton: needs, questions, structure, draft, readability, cut list
- [`scripts/readability.py`](scripts/readability.py) — stdlib plain-language check: sentence length, long words, estimated grade, over-length sentences
- [`examples/parking-permit-page.md`](examples/parking-permit-page.md) — worked example: a council page rewritten from a policy paragraph, with real script output

## Quality bar

- **Every need names a specific reader, a need and an outcome**, with an evidence tag.
- **Questions are ranked, and the page order follows the ranking.** The top question is answered in the first two sentences.
- **Headings are in the reader's words.**
- **The draft keeps every fact from the source**, and every change of meaning is flagged. Plain language never changes a rule.
- **No sentence over 25 words** in the draft, and the script's before/after numbers are reported as it printed them.
- **The cut list accounts for everything removed**, with a reason each.
- **Nothing is invented.** Fees, deadlines, eligibility and contact details not in the source are `{placeholder}`s listed in open questions.

## When to use this skill

- ✅ A new page or journey that needs its content worked out from user needs
- ✅ "Rewrite this in plain English" for a policy, service or product page
- ✅ A long page nobody reads, with support tickets asking things the page already says
- ✅ Agreeing what a page is for before design or development starts

## When NOT to use this skill

- ❌ Button labels, errors, empty states and other interface strings — that's `ux-writing`
- ❌ A step-by-step setup guide, walkthrough or API reference — that's `guide-builder`
- ❌ Where pages live and how the navigation groups them — that's `information-architecture`
- ❌ The persona's whole path and emotions across stages — that's `user-journey-map`

## Anti-patterns to avoid

- ❌ **Starting from what the organisation wants to say.** "About our scheme" as the first section; readers want to know if they qualify.
- ❌ **"As a user, I need information."** No specific reader, no outcome, and no way to tell whether the page met the need.
- ❌ **Plain language that changes the rule.** "You'll get it in a week" when the policy says "up to 10 working days".
- ❌ **Dumbing down for specialists.** Plain language for clinicians keeps clinical terms and cuts the padding.
- ❌ **Silent cuts.** Deleting the paragraph a lawyer insisted on, without noting it, gets the whole rewrite rejected.
- ❌ **Quoting the grade as gospel.** A readability formula counts syllables. It can't tell whether the page answers the reader's question.
- ❌ **One page for three tasks.** "Permits, fines and appeals" on one page serves none of them well. Split it.

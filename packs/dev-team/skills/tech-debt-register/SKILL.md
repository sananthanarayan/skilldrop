---
name: tech-debt-register
description: Turn a pile of technical-debt complaints, TODOs and incident notes into a ranked register: each item with where it lives, the cost it imposes today backed by evidence, the size of the fix, a decision (pay now, schedule, accept or watch) with the trigger that reopens it, and an owner if one was given. It ends with the few items worth paying down this quarter and why. Use when the user asks for a tech debt register, a debt inventory or backlog, "what debt should we pay down", "prioritise our tech debt", or wants to make the case for refactoring time.
---

# tech-debt-register

You turn complaints about the codebase into a register a team can decide from. Debt is
something that costs the team now, every week, until it is fixed. The register says what
each item costs, what fixing it takes, and what to do about it, and it is short enough to
be read in a planning meeting.

## How to respond

1. **Gather the items from what you were given.** Notes, a TODO or FIXME list, incident
   write-ups, a ticket export, the user's own list. In a repository you may also search for
   `TODO`, `FIXME`, `HACK` and skipped tests, and say that you did. Merge items that
   describe the same underlying problem and keep the count of what was merged.

2. **Write each item as a thing with a place.** ✅ "Order export builds CSV by string
   concatenation in `export/orders.py`; breaks on commas in customer names." ❌ "Code
   quality is poor." ❌ "Needs refactoring." An item you cannot locate goes under
   *Unlocated*, with the question that would locate it.

3. **State the cost it imposes today, with the evidence.** This is the interest. Use what
   the input shows: incidents caused, hours lost, a slow build time, a recurring bug, a
   workaround every new joiner has to learn. Quote or cite it. When the input shows no
   cost, write `no evidence of cost` and do not guess one. An item with no observable cost
   is a preference; keep it in the register, at the bottom.

   The user's own statement counts as evidence of a cost, marked `reported, not measured`:
   "deploys take ages" and "tests are flaky" are costs someone is paying. Record them as
   reported, say what measurement would confirm them, and still rank them.

4. **Size the fix.** S (under two days), M (up to two weeks), L (more). Use the team's own
   estimate when they gave one. Add what the fix depends on and what it puts at risk.

5. **Decide, one of four, with a reason in a clause:**
   - **Pay now**: high, evidenced cost and a fix the team can finish this quarter.
   - **Schedule**: real cost, but the fix is large or blocked; name what it waits on.
   - **Accept**: the cost is small or the code is going away; say for how long.
   - **Watch**: no cost reported or shown; name the signal that would promote it.

   Don't hide behind Watch. A list where every item is Watch is not a register. When costs
   are reported but unmeasured, still pick an order and one or two candidates to pay down,
   label the ranking `provisional`, and say which single measurement would change it.

   Every item gets a **trigger**: the event that reopens the decision ("a second export
   incident", "the service passes 50 req/s"). Not a date alone.

6. **Rank by cost against size.** Evidenced, recurring cost with a small fix first. Do not
   produce a numeric score that the input cannot support; order the list and say in one
   line why the top items are on top.

7. **Write the register.** A table with these columns: `ID`, `Item`, `Where`,
   `Cost today (evidence)`, `Fix size`, `Decision`, `Trigger`, `Owner`. Owner is filled only
   when the input names one; otherwise `unassigned`. When you can write files, save it as
   `tech-debt-register.md` so the team can keep it, and show the lead-in and the table in
   the reply as well. Add a CSV with the same columns when the user asks for one.

8. **Lead with the decision.** Above the table, in this order: the three or fewer items to
   pay down this quarter and the cost each removes; what was merged, and what was left
   unlocated or without evidence; the one question whose answer would most change the
   ranking.

**With nothing to work from** (no items, no repository, no notes), ask for the list in one
line. With a thin list, build the register from it, mark what is unknown as unknown, and
say what evidence would firm it up. Do not pad it with debt the input never mentioned.

## Quality bar

- **Every cost has evidence or says it has none.** No invented hours, incident counts,
  percentages or money.
- **Every item has a place** or is listed as unlocated.
- **Every item has a decision and a trigger.**
- **The top of the list is defensible**: evidenced cost, fix the team can finish.
- **It fits a planning meeting.** One table, one short lead-in.

## When to use this skill

- ✅ Making the case for refactoring time with something better than "the code is messy"
- ✅ Quarterly planning: which debt to pay down and which to live with
- ✅ Turning a TODO grep, incident notes or a rant into a ranked, decided list

## When NOT to use this skill

- ❌ Planning how to carry out one large change. Use `migration-plan`.
- ❌ Sorting incoming bug reports. Use `bug-triage`.
- ❌ Cleaning up a tracker backlog of mixed work. Use `backlog-triage`.
- ❌ Business or delivery risks that are not about the code. Use `risk-register`.

## Anti-patterns to avoid

- ❌ **Invented numbers.** "Costs about 6 hours a week" with nothing behind it is a guess
  that will be quoted in a planning deck.
- ❌ **Everything is high priority.** If most items are "pay now", none are.
- ❌ **Everything is Watch.** Declining to rank because nothing was measured hands the
  decision back unmade.
- ❌ **Listing preferences as debt.** "Should be in TypeScript" with no cost is a wish.
- ❌ **A weighted score to two decimals.** False precision over thin evidence.
- ❌ **Padding.** Adding generic debt ("improve test coverage") that nobody raised.
- ❌ **Showing the machinery.** The register is for the team: no mention of this skill or
  how it was produced.

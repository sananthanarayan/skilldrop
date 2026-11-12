---
name: vesting-schedule
description: Work out vesting for founder stock, restricted stock, options and RSUs — each grant's cliff date and amount, every vesting date in whole shares, what is vested on any date, what happens when someone leaves (vested, forfeited or repurchasable, and the last day to exercise), single- and double-trigger acceleration on a sale, and the US 83(b) election deadline moved past weekends and holidays — computed by a script that keeps the totals exact. Use when a founder asks "how much has my co-founder vested", "what happens to her shares if she leaves", "when does the cliff hit", "build our vesting schedule", "when is the 83(b) deadline", or "what does double-trigger acceleration give us in a sale".
---

# vesting-schedule

Founders and early employees ask the same questions at the worst moments: a co-founder is
leaving, an acquirer is asking, a grant was signed last week and nobody remembers the 83(b).
The answers are date arithmetic that is easy to get wrong in ways that matter: a vesting start
on the 31st in a month with 30 days, a cliff that falls between two quarterly dates, rounding
that runs ahead of the grant, a 30-day deadline that lands on the Fourth of July. A script
computes every grant exactly; the agent turns the founder's documents into its input and the
result into the answer they need.

## How to respond

**These rules come before the steps and outrank them:**

- **Answer the question asked, first.** ✅ *"If Sam leaves on 20 August, 45,000 of their
  120,000 options have vested and the other 75,000 lapse. They have until 18 November to
  exercise."* Never mention a script, a JSON file, this skill's name, a path inside its folder
  or a temporary path, and never call your work "the check" or "a tool".
- **Every share count and date comes from the computed schedule,** run on the final inputs.
  Each scenario the person asks about (a leaving date, a closing date, "what if she's let go
  in July instead") is its own run with that date. Never count months by hand: a 30-month
  answer written as 31 is the commonest error in this work.
- **Stay on the questions asked,** in their order, and answer each fully. For a leaver that
  means what happens to the unvested shares: who can buy them back, at what price if the
  documents say, and the deadline for doing it as a date, against today's date, plus the last
  day to exercise vested options.
- **The 83(b) deadline is never approximate.** Give the date, say it is 30 days from the grant
  (or from an early exercise), and when day 30 falls on a weekend or federal holiday, say that
  the deadline moves to the next business day and advise filing well before day 30 anyway.
  When it has passed, say so plainly and what that means: the shares are taxed as they vest
  instead of at grant. Recommend a tax adviser only for what to do next, not for the date.
- **Say which terms you assumed.** The vesting start (often earlier than the grant date), the
  cliff, monthly or quarterly vesting, the exercise window after leaving (90 days is usual), the
  company's buy-back window, what counts as a "good reason" resignation for double-trigger, and
  how acceleration is ordered (single trigger here applies to what is unvested at the sale;
  documents sometimes accelerate from the end of the schedule instead). Tag each `[assumption]` and
  give the figure under the other reading when it changes the answer.
- **Name what is worth a lawyer's hour, and only that.** One or two lines: a leaver dispute,
  acceleration terms an acquirer is pushing back on, a missed 83(b). Never refuse, never open
  with a disclaimer.
- **Working files stay out of sight.** The input goes in a private temporary folder
  (`mktemp -d`) and is deleted before replying. A spreadsheet they asked for goes in their
  working directory under a plain name.

1. **Gather each grant** from the documents or the conversation: holder, type (founder stock,
   restricted stock, option, RSU), shares, grant date, vesting start, months, cliff, frequency,
   acceleration (single trigger: on a sale; double trigger: a sale and then losing the job within
   a window), any leaving date, any early exercise, and whether an 83(b) was filed. Defaults
   when unsaid: 48 months, a 12-month cliff, monthly, US. Ask at most two questions, only for a
   missing share count or start date.

2. **Write the input** in the shape of [`templates/vesting.json`](templates/vesting.json). A sale
   goes in `change_of_control` at the top.

3. **Run it** on the date they care about (today, a leaving date, a closing date).

   ```bash
   work=$(mktemp -d 2>/dev/null || mktemp -d ./.work.XXXXXX)   # a private folder for this run only
   # Claude Code
   python3 "${CLAUDE_SKILL_DIR}/scripts/vesting.py" "$work/vesting.json" --as-of 2027-06-30
   # Other IDEs (from the skill folder); --csv writes every vesting date
   python3 scripts/vesting.py "$work/vesting.json" --csv vesting-schedule.csv --full
   ```

   Exit 0 means computed, 1 means a check failed (a schedule that doesn't sum to its grant, or a
   passed 83(b) deadline), 2 means the input can't be read. Rerun with the other reading of any
   assumption that changes the answer.

4. **Reply in this order:**
   1. **The answer** to their question, with the numbers and dates.
   2. **Each grant's summary:** cliff date and amount, fully vested date, vested and unvested now.
   3. **Deadlines:** 83(b) dates, last days to exercise.
   4. **The schedule,** yearly in the reply (every date in a spreadsheet when asked).
   5. **Assumptions,** one line each.
   6. **What to have a lawyer or tax adviser look at,** one or two lines.

**Non-interactive runs** (subagent, CI, headless): unsaid terms take the defaults above, tagged
`[assumption]`. With no share count or no start date for a grant, emit `BLOCKED: need each
grant's shares and vesting start date`.

## Useful references in this skill

- [`templates/vesting.json`](templates/vesting.json) — the input: a founder with double-trigger acceleration, an engineer who leaves, an advisor on quarterly vesting
- [`scripts/vesting.py`](scripts/vesting.py) — cliffs, month-end dates, whole-share rounding, leavers, acceleration, 83(b) deadlines with US holidays
- [`examples/cofounder-leaving.md`](examples/cofounder-leaving.md) — worked example: a co-founder leaving 14 months in, with a missed 83(b) question

## Quality bar

- **Every share count and date comes from the computed schedule,** and each grant's dates sum to its shares.
- **A start on the 29th–31st vests on the last day of shorter months,** and leap years count.
- **The 83(b) deadline is an exact date,** moved past weekends and federal holidays, and a passed one is said plainly.
- **Leaving gives vested, unvested and the exercise deadline,** each from the leaving date, not today.
- **Every assumed term is stated,** with the other reading's figure when it changes the answer.
- **The reply answers the question first,** with no mention of scripts or files.

## When to use this skill

- ✅ A co-founder or early employee is leaving and everyone needs the numbers
- ✅ A new grant was signed: when does it cliff, and when is the 83(b) due
- ✅ An acquirer or investor asks what vests on a sale
- ✅ Building the schedule for a founder agreement or an option plan

## When NOT to use this skill

- ❌ Tax: what an 83(b) or an exercise costs, ISOs against NSOs, EMI or ESOP rules
- ❌ Ownership after a funding round: that's a cap table
- ❌ Drafting the stock purchase or option agreement
- ❌ Valuing the shares or setting a strike price

## Anti-patterns to avoid

- ❌ **"About 30 days from the grant."** The 83(b) date is exact, and a weekend moves it.
- ❌ **Vesting from the grant date when the agreement says an earlier start.** Founders often backdate the start to when they began.
- ❌ **Rounding each month up.** A schedule of 2,500.4 shares a month that rounds up overshoots the grant; round the running total down and settle on the last date.
- ❌ **Treating double-trigger as automatic on a sale.** It needs the second trigger.
- ❌ **Counting the leaver's vesting to today** instead of to their leaving date.
- ❌ **"The schedule shows…"** The founder wants the number.

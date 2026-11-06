---
name: cap-table
description: Work out who owns what in a startup through its SAFEs, convertible notes and a priced round — each SAFE's and note's conversion price and whether its cap or discount applied, the price per share, the option-pool top-up and who it dilutes, the fully diluted cap table before and after, and founder ownership at other valuations — computed by a script that checks the post-money and the 100 % total. Use when a founder asks "how much of my company will I own after this round", "model our SAFEs converting", "what does this term sheet do to our cap table", "how much have I given away in SAFEs", or "compare a $12M and a $16M pre-money".
---

# cap-table

The numbers a founder needs before signing a term sheet or another SAFE: what each investor
ends up with, what the option pool top-up really costs, and how much of the company the
founders keep. A capable agent gets the simple case right and the real one wrong: a stack of
post-money SAFEs at different caps, a pre-money SAFE beside them, a note accruing interest,
and a pool top-up the lead investor wants in the pre-money. A script solves the round exactly,
including the circularity where the SAFEs' shares depend on the price and the price on the
SAFEs, and checks that the post-money equals price × shares and ownership sums to 100 %.

## How to respond

**These rules come before the steps and outrank them:**

- **Answer the founder first, in a founder's words.** Lead with the number they asked for:
  ✅ *"After the round you each own 28.3 %, down from 45 % today. The pool top-up costs you
  about $1.1M of the headline $16M."* Never mention a script, a JSON file, this skill's name
  or a path inside its folder, never call your work "the check" or "a tool", and never show
  a temporary path.
- **Every number in the reply comes from the computed cap table,** run on the final inputs.
  Never do conversion arithmetic in your head, and never round a percentage the table didn't.
- **Say which terms you assumed, and which way each one cuts.** A SAFE's type (post-money or
  pre-money), whether the pool top-up sits in the pre-money, and when interest stops are the
  terms that move founder ownership the most. When the founder didn't say, use the default
  below, tag it `[assumption]`, and give the figure under the other reading when it changes
  the founder's stake by more than half a point.
- **Name what is worth a lawyer's hour, and only that.** One or two lines, specific to this
  round: ✅ *"Before you sign: have counsel confirm whether the 10 % pool is pre- or
  post-money in the term sheet — it moves you by 2.4 points."* Never refuse, never open with
  a disclaimer, never pad with "this is not legal advice".
- **Working files stay out of sight.** Write the input to a private folder made for this run
  (`mktemp -d`, never a fixed path) and delete it before replying. A spreadsheet the founder
  asked for goes in their working directory under a plain name. Never overwrite a file they
  gave you.
- **Their cap table comes back in its own shape.** Given a spreadsheet or table, return the
  after-round table with the same columns and holder order, with new rows added at the end.

1. **Gather the inputs.** From the conversation or the files named (a cap table export, a
   SAFE, a term sheet):
   - **Shareholders:** each holder's shares today (founders, employees, early common).
   - **Options:** granted and outstanding, and the unissued pool.
   - **Each SAFE:** amount, valuation cap, discount, post-money or pre-money, MFN.
   - **Each note:** principal, interest rate, issue date, cap, discount.
   - **The round,** if there is one: pre-money valuation, each new investor's amount, the
     option pool target after the round, the closing date.

   Defaults when unsaid: a SAFE signed from 2018 on is post-money (YC's current form); a SAFE
   with only a cap converts at the cap; the pool target is in the pre-money (the usual term
   sheet); note interest is simple and runs to closing. Ask at most two questions, and only
   for a missing share count or SAFE amount, which no default can stand in for.

2. **Write the input** in the shape of [`templates/cap.json`](templates/cap.json): `holders`,
   `options`, `safes` (with `type`: `post` or `pre`), `notes`, and `round`. Discounts and the
   pool target are fractions (`0.2`) or percents (`20`).

3. **Run it.**

   ```bash
   work=$(mktemp -d 2>/dev/null || mktemp -d ./.work.XXXXXX)   # a private folder for this run only
   # Claude Code
   python3 "${CLAUDE_SKILL_DIR}/scripts/cap_table.py" "$work/cap.json" --scenarios 12m,16m,20m
   # Other IDEs (from the skill folder); --csv writes the after-round table for a spreadsheet
   python3 scripts/cap_table.py "$work/cap.json" --csv cap-table-after-series-a.csv
   ```

   Exit 0 means computed, 1 means a check failed or the round can't settle (the SAFEs' caps
   leave no room at that valuation, which is itself the answer), and 2 means the input can't
   be read. Read every `WARN`: an MFN SAFE with no terms of its own, interest left out for a
   missing date.

4. **Run it again for each assumption that matters.** Flip the SAFE type, or move the pool
   to post-money, and keep the figures from both runs for the reply.

5. **Reply in this order:**
   1. **The answer** to what they asked, in one or two sentences, with each founder's stake
      before and after.
   2. **The cap table after the round** as a table: holder, shares, percent.
   3. **What each SAFE and note converted at,** and whether its cap or its discount set the price.
   4. **What the pool top-up costs the existing holders:** the headline pre-money against the
      effective one.
   5. **Other valuations,** when they asked or when the round is being negotiated.
   6. **Assumptions,** one line each, with what changes under the other reading.
   7. **What to have a lawyer confirm,** one or two lines.

**Non-interactive runs** (subagent, CI, headless): unsaid terms take the defaults above, each
tagged `[assumption]`. With no share counts at all, emit `BLOCKED: need each shareholder's
shares (or the cap table export) and each SAFE's amount and cap`.

## Useful references in this skill

- [`templates/cap.json`](templates/cap.json) — the input: two founders, a pool, three SAFEs of mixed types, a note and a Series A
- [`scripts/cap_table.py`](scripts/cap_table.py) — solves the round, conversion by cap or discount, pool top-up, scenarios, and checks the totals
- [`examples/seed-to-series-a.md`](examples/seed-to-series-a.md) — worked example: three SAFEs and a note into a Series A, and what the pool top-up really cost

## Quality bar

- **Every figure comes from the computed table,** and the post-money equals price × fully diluted shares.
- **Each SAFE and note shows its conversion price and what set it,** cap or discount.
- **The pool top-up's cost is stated in money,** not only in shares.
- **Every unsaid term is a stated assumption,** with the other reading's figure when it moves the founders by more than half a point.
- **The reply leads with the founders' ownership,** in plain words, with no mention of scripts or files.
- **At most two lawyer lines,** each specific to this round.

## When to use this skill

- ✅ A term sheet arrived and the founders want to know what they keep
- ✅ Raising another SAFE and checking what the stack already gives away
- ✅ Comparing two offers, or two valuations, on founder ownership
- ✅ Explaining to a co-founder or an early employee what the round does to their stake

## When NOT to use this skill

- ❌ Valuing the company: this takes the valuation as given
- ❌ Tax on options or shares (83(b) elections, ISOs, EMI schemes): ask a tax adviser
- ❌ Liquidation waterfalls on an exit: this models ownership, not who is paid first in a sale
- ❌ Drafting the SAFE or the term sheet itself

## Anti-patterns to avoid

- ❌ **Treating a post-money SAFE like a pre-money one.** A $500k post-money SAFE at an $8M cap is 6.25 % before the round; under the old pre-money form it is less, and founders bear the difference.
- ❌ **Forgetting the pool top-up comes out of the founders.** A 10 % post-money pool in the pre-money turns a $16M headline into about $14.9M for the existing holders.
- ❌ **Converting a note on its principal.** Eighteen months at 6 % is 9 % more shares.
- ❌ **Applying the discount and the cap together.** The SAFE takes whichever gives the lower price, not both.
- ❌ **A percentage table that sums to 99.7 %.** The check catches it; a hand-built one doesn't.
- ❌ **"This is not legal advice" as an opening line.** Say what to have checked, specifically, at the end.
- ❌ **"The script shows…"** The founder wants their percentage.

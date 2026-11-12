---
name: lease-check
description: Check a commercial lease before a startup signs it for its first office, studio or lab — a script turns the lease's terms into every date and sum the tenant must plan around (rent year by year through stepped rents, fixed and index-linked reviews with caps and collars, rent-free months, what the company is committed to pay up to each break and to the end, and each break, renewal and notice deadline as a date), then flags terms that can't all be true and deadlines already passed — and reads the lease for the clauses that hurt a small tenant. Use when a founder says "review this office lease", "what's our break clause notice date", "how much are we committing to on this lease", "check this lease before I sign", "when can we get out of this lease", or "what does the rent review do".
---

# lease-check

A first office lease is often the biggest commitment a young company signs, and founders sign
it on the headline rent. What hurts is in the detail. The break clause needs six months'
notice and any unpaid sum voids it. The CPI review compounds three years at once. The rent-free
months are forfeited if the break is used. Repair obligations hand the tenant the roof. A
script turns the lease's terms into the numbers: every deadline as a date, the rent each year,
and what the company has committed to pay up to each exit. The agent reads the lease from the
tenant's side.

## How to respond

**These rules come before the steps and outrank them:**

- **Lead with the commitment and the exits, in a founder's words.** ✅ *"Signing commits you
  to £113,400 up to the break in January 2030. To use the break you must give notice by 1 July
  2029 and have paid everything, down to the last service-charge invoice, or the break fails
  and you're in to 2031 for another £90,590."* Never mention a script, a JSON file, this
  skill's name, a path inside its folder or a temporary path, and never call your work "the
  check" or "a tool".
- **Every date and sum comes from the computed terms,** with the clause behind it.
- **Read for the tenant's side,** and give the wording to ask for on each problem, ready to
  paste into an email to the agent or landlord.
- **Say what the terms can't price:** an open-market review, a service charge with no cap,
  dilapidations at the end. Name each one, and suggest the ask that bounds it.
- **Name what is worth a lawyer's hour, and only that.** One or two lines: a personal
  guarantee, full repairing terms on an old building, a break with conditions the landlord
  won't soften, or a lease outside the protection of business-tenancy law where that applies.
  Never refuse, never open with a disclaimer.
- **Working files stay out of sight.** The terms you extract go in a private temporary folder
  (`mktemp -d`) and are deleted before replying. Never overwrite their lease.

1. **Read the lease or heads of terms** and extract: start date, term in months, starting
   rent, how it's paid, rent-free months, stepped rents, each rent review (month, type, any
   cap, collar, upward-only), service charge and any cap, deposit, each break (month, notice,
   who can break, conditions, any penalty), renewal option, notice to leave. Write down the
   clause for each.

2. **Write the terms** in the shape of [`templates/terms.json`](templates/terms.json). An
   index-linked review over several years takes `years` so the cap and collar compound the way
   the lease says; check the lease's wording, which differs on this. When the lease names a
   break by its day ("the last day of the third year" is 28 February; "the third anniversary"
   is 1 March), give it as the break's `date`: the notice date follows from it.

3. **Run it** on today's date, so passed deadlines are flagged.

   ```bash
   work=$(mktemp -d 2>/dev/null || mktemp -d ./.work.XXXXXX)   # a private folder for this run only
   # Claude Code
   python3 "${CLAUDE_SKILL_DIR}/scripts/lease_terms.py" "$work/terms.json" --as-of 2026-11-08
   # Other IDEs (from the skill folder)
   python3 scripts/lease_terms.py "$work/terms.json"
   ```

   Exit 0 means computed, 1 means a deadline has passed or the terms contradict each other (a
   break after the end, a notice that runs back before the start, rent-free as long as the
   term), and 2 means the input can't be read.

4. **Read the lease for the tenant** against [`reference.md`](reference.md): break conditions,
   repair and reinstatement, dilapidations, service charge, alienation (subletting, assignment,
   sharing with a group company), use, alterations, guarantees and rent deposits, insurance,
   and whether the rent-free survives a break. For each problem: clause, why it hurts, wording
   to ask for. Mark severity: 🟥 don't sign as is, 🟧 push back, 🟨 worth asking.

5. **Reply in this order:**
   1. **The commitment and the exits:** what signing commits to up to each break and to the
      end, and the notice date for each break.
   2. **Fixes before signing,** most severe first, with wording to ask for.
   3. **Deadlines to diarise,** each as a date with its clause.
   4. **Rent by year,** and what can't be priced yet.
   5. **What to have a lawyer look at,** one or two lines.

**Non-interactive runs** (subagent, CI, headless): unsaid terms are left out and named as
missing, never filled with a typical value. With no start date, term or rent, emit `BLOCKED:
need the lease (or heads of terms) with its start date, length and rent`.

## Useful references in this skill

- [`reference.md`](reference.md) — the lease clauses that hurt a small tenant, and what to ask for in each
- [`templates/terms.json`](templates/terms.json) — the input: a five-year lease with rent-free, a capped CPI review and a conditional break
- [`scripts/lease_terms.py`](scripts/lease_terms.py) — rent by year through reviews, committed cost to each break and the end, deadlines, contradictions
- [`examples/first-office.md`](examples/first-office.md) — worked example: heads of terms for a first office, and what the break really costs

## Quality bar

- **The committed cost to each break and to the end is a sum,** rent and service charge, after rent-free.
- **Every deadline is a date with its clause,** and a passed one is said plainly.
- **Index-linked reviews compound the way the lease says,** within its cap and collar, and upward-only is applied.
- **What can't be priced is named,** with the ask that bounds it.
- **Every problem has the wording to ask for.**
- **The reply leads with the commitment and the exits,** with no mention of scripts or files.

## When to use this skill

- ✅ Heads of terms or a draft lease for a first office, studio, lab or shop
- ✅ "When can we get out of this lease, and what does it cost to stay till then?"
- ✅ A rent review letter, or a break date coming up
- ✅ Comparing two buildings on what each really commits the company to

## When NOT to use this skill

- ❌ A coworking membership with monthly terms: read its notice period, no schedule needed
- ❌ Residential tenancies
- ❌ A dispute with a landlord, or a dilapidations claim already made: get a surveyor or a lawyer
- ❌ Buying a property

## Anti-patterns to avoid

- ❌ **Quoting the headline rent as the cost.** Rent-free, reviews and service charge move it; give the committed sum.
- ❌ **"The break is in year three."** The notice date is what matters, and it's six months earlier.
- ❌ **Treating a conditional break as certain.** One unpaid invoice can void it.
- ❌ **Compounding a three-year CPI review as one year,** or ignoring its cap.
- ❌ **Missing that rent-free is clawed back** if the break is used, when the lease says so.
- ❌ **"The calculation shows…"** The founder wants the sum and the date.

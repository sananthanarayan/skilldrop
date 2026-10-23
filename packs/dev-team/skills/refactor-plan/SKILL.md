---
name: refactor-plan
description: Plan paying down one piece of technical debt as a refactor that serves the goal it is blocking — characterisation tests on the riskiest behaviour first, then small steps each merged to main with main releasable after every one, pure refactors kept apart from the behaviour changes the goal needs, a scope fence, a stop point, a technique per step (extract, branch by abstraction, parallel change, strangler fig, mikado) and the clashes with in-flight feature work. Use when the user asks for a refactor plan, how to untangle, break up, replace or clean up a module without a rewrite, how to pay down a tech-debt item, "how do we refactor X without stopping feature work", "how do we get off X without a big bang", or wants a strangler-fig or mikado plan.
---

# refactor-plan

You plan a refactor: work that pays down one piece of technical debt so that something the
user wants becomes safe to do — add a shipping zone without fear, retire a vendor before its
contract ends, let a batch worker import billing. The plan is a sequence of small steps, each
one PR merged to main with main releasable after it, ending at the structure that goal needs.
The team can stop after any step and the code is better than it was.

Recording and ranking debt is `tech-debt-register`'s job; this skill starts from one item.
Moving data or a schema with a backfill is `migration-plan`'s; when the payoff needs one, the
plan stops at the code seam and names the migration as separate work.

## How to respond

**Four rules come before the steps and outrank them:**

- **Lead with the answer.** The first two lines say the approach and the first step, in plain words: ✅ *"Put an interface in front of `SmsGateway`, build the new client behind it dark, and move message types over one flag at a time. Start with characterisation tests for `SmsGateway.send` in a new test file."* — ❌ a title, a target table, or a paragraph of context first.
- **Match the size of the ask.** A question in chat ("how do we do this??", "plan how we untangle X") gets the plan in the reply: what the code shows, then a numbered sequence, one or two lines a step, each with its why. Write a full document only when the user asks for one (a file, "a proper plan", something to take to planning) or the work runs past about ten steps; then write the file and reply with the lead, the findings that change the plan, and where the file is. Never both at full length.
- **Read what you were given, and use only that.** Open every file the user names and the callers it imports or is imported by. Report what is actually there, cited as `file:function`. Never say a file is unreadable without having tried to open it; if a read really fails, say which file and plan without it. No invented modules, baselines, vendors, volumes or dates. Callers or facts not in the input are checks to run (✅ *"grep for `price_order(` and `lines=`"*), not statements.
- **Write for someone who has never heard of this skill.** No skill names, no scripts or paths from this folder, nothing about how the plan was produced. With a debt item to work on, state assumptions in a line and produce the plan; with nothing at all, ask for the debt item in one or two plain sentences.

1. **Map the debt from the code.** The functions involved, every caller, and what each caller
   relies on beyond the return value. Look for these four; they are what a plain read misses
   and what breaks a refactor:
   - **Contracts callers depend on:** mutation of an argument (✅ *"`exports/ledger.py:month_end` reads the rounding line back out of the `lines` list it passed to `price_order`, so `price_order` must keep appending to it"*), a return value that lies (✅ *"`SmsGateway.send` returns `True` from its `except`, so the retry in `alerts/notify.py:page_oncall` has never fired"*), ordering, side effects.
   - **Copies outside the module:** duplicated constants or logic that bypass it and have drifted (a cron script with its own HTTP send, a report with its own `VAT_RATES`). Search every file in the input, scripts and reports included, for the module's constant and function names. Each goes inside or outside the fence by name; if outside, the plan does not claim the duplication is gone.
   - **Test coverage as it is:** which paths existing tests reach (✅ *"the only test covers `format_message()`"*; ✅ *"`test_checkout.py` never imports `pricing.py`"*).
   - **Stale signals:** a comment, TODO or open PR that says one thing while the code does another.

2. **Start from the goal, and end at the structure it needs.** Name the user's stated goal and
   the end state that delivers it — not the same code split across more files.
   ✅ *"Goal: adding a shipping zone is a one-line data change. End state: zone rules live in
   one table that `quote_shipping` reads; a new zone is a row plus a test."* — ❌ *"Extract
   seven helpers from `quote_shipping` unchanged"* and stop. Then the target: one metric the team
   can read (from the register item, or files touched per change, call sites on the old path,
   forbidden imports), its baseline from the input or `not measured` with a step to measure it,
   and a checkable **stop point** (✅ *"zero sends through the old gateway, the cron script
   included"* — ❌ *"when the code is clean"*). Every step must move toward that end state;
   a step that doesn't is cut.

3. **Label every step `refactor` or `behaviour change`.** A refactor keeps output identical and
   is proven by the pinned tests. A behaviour change the goal needs (moving rules into data
   that changes a result, removing a mutation a caller relied on, surfacing errors that were
   swallowed, switching traffic to a new provider) is its own step, placed after the refactor
   that makes it safe, with the caller moved first and its own rollback. Behaviour changes the
   goal does not need — renamed env vars, a fixed rounding bug, money as Decimal, a schema
   change — go out of the plan to a ticket, a later parallel change or a migration. Bugs callers
   depend on are pinned as they are: ✅ *"pin `send` returning `true` on failure; surfacing
   failures is a later, deliberate step"* — ❌ *"fix it while writing the test."*

4. **Characterisation tests first, on the riskiest behaviour.** Before any step touches
   untested code, pin current output, starting with what has caused incidents or what the code
   comments warn about (the register's incidents, branches with odd rules). Name each behaviour
   to pin by function: inputs callers send, boundaries (empty, zero, rounding, ordering,
   timezones), error paths, current bugs. An approval (golden-master) test over recorded
   real-shape inputs when output is too wide to assert by hand. Pin at the narrowest seam that
   runs without the current suite's infrastructure.
   **An open PR on the same file never delays the tests.** Tests change no production code: put
   them in a new test file so they can't conflict, and if the open PR changes the pinned
   behaviour on purpose, its author updates the pinned value in that PR. ❌ *"Characterisation
   tests for the zone rules after #212 merges"* leaves the incident-prone code bare for weeks.
   Code already covered on the paths a step touches skips this step; say which tests cover it.

5. **Cut steps by the one-PR rule.** One PR a reviewer reads in one sitting, merged within a
   couple of days, main releasable after it. **Never mix a move with a change** (✅ *"PR A: move
   `calculate_tax` to `orders/tax.py` unchanged, old name re-exports it. PR B: change it."*).
   **No long-lived branch:** work that can't merge in days goes behind a seam, on main and dark.
   Size the sequence against the delivery facts given (CI time and flake rate, deploys per week,
   approval gates, a deadline): ✅ *"about two deploys a week leaves roughly N releases before
   the deadline; each flag flip needs one, so flips start by week X"* — counted from the input,
   never invented. Around a busy window (peak season, a launch), run the dark refactor steps
   through it and schedule the behaviour-change steps after it.

6. **Pick the technique per step and say why** in one clause. The catalogue, with rollback
   for each, is in [`reference.md`](reference.md):

   | Technique | Use when |
   |---|---|
   | Characterisation tests | The code a step touches has no tests on the paths callers use |
   | Extract / inline / move | A cohesive piece can leave in one PR with callers unchanged |
   | Branch by abstraction | A dependency many callers use must be replaced, and the swap takes more than one PR |
   | Parallel change (expand–contract) | A signature, contract or data shape changes and callers move over several PRs |
   | Strangler fig | A whole module is replaced piece by piece, with routing at its edge deciding old or new per call |
   | Mikado method | Each attempted change breaks on prerequisites; the graph of what must change first is unknown |

7. **Order for value early, stoppable everywhere.** After the tests, the first step is the one
   that unblocks the work the user named, not the neatest one; say why it is first. Every step
   leaves the code better on its own. A step that only pays off once a later one lands is merged
   with it, or its pair is within the next two steps and the plan says two paths exist until then.

8. **Coordinate with in-flight work.** For each open PR or planned feature, name the shared
   `file:function` and pick one:
   - **Land first** — a PR the business needs (peak season, a customer date) merges ahead; the refactor rebases.
   - **Wait** — a *move or rewrite* of code an open PR edits starts after it merges. Tests and seams elsewhere carry on.
   - **Fold in** — the feature PR does the extraction for its own area, as a separate commit, when one team owns both.
   - **Through the seam** — a PR adding a new caller of the code being replaced is asked to call the new interface.
   - **Freeze window** — hours, not weeks, announced, for a high-churn move nobody can work around.
   The refactor absorbs the rebase cost, not the feature. With no in-flight list, say
   `[assumption] no known clashes` and add "check open PRs on these files before each step".

9. **Emit the plan in the shape rule two chose.**
   - **Chat reply** (default): the two-line lead; "What the code shows" as three to six bullets
     citing `file:function`; the numbered steps, each one or two lines — the change, the why,
     `[refactor]` or `[behaviour change]`, and the clash or rollback when it matters; one line
     each for target and stop point and for not touched; at most three questions under "To
     confirm". Aim under about 50 lines.
   - **Document** (asked for, or large): the skeleton in
     [`templates/refactor-plan.md`](templates/refactor-plan.md), each step with change,
     type, technique and why, verified by, rollback (the live side for any flag), risk, size,
     owner role. Save it where the user asked; the reply is the lead, the findings and the path.
   Either shape ends with the scope-creep rule in one line: *"Anything found during the work
   that isn't in a step goes to the debt register as a new item."*

**Non-interactive runs** (subagent, CI, headless): with no debt item, module or pain named at
all, emit `BLOCKED: need the debt to pay down — the module or register item and what it costs
the team`. Everything else degrades to `[assumption]`: a missing baseline becomes a measuring
step, missing code means steps cite only the names given, a missing in-flight list becomes
"no known clashes", a missing owner becomes a role.

## Useful references in this skill

- [`reference.md`](reference.md) — the technique catalogue: when each fits, the step shape, rollback and "which side is live", the failure mode of each
- [`templates/refactor-plan.md`](templates/refactor-plan.md) — the chat shape and the document skeleton
- [`examples/search-ranker.md`](examples/search-ranker.md) — worked example: a 600-line ranking function with a flag pile and an in-flight PR, as a chat reply and as a document

## Quality bar

- **The first two lines give the approach and the first step.** A chat question gets a chat-sized plan; a document only when asked or large.
- **Every step serves the stated goal,** and the last step reaches the structure that goal needs.
- **Every step is labelled refactor or behaviour change;** behaviour changes stand alone, after the refactor that makes them safe.
- **Characterisation tests come first, on the incident-prone behaviour,** and no open PR leaves that behaviour unpinned.
- **Caller contracts, copies outside the module and real test coverage are reported** from the files, cited `file:function`.
- **Every in-flight clash has a decision,** and a must-land feature PR is never blocked.
- **The scope fence and stop point exist;** new findings go to the register.
- **Every file, function, metric and number is from the input.** Unknowns are checks to run.

## When to use this skill

- ✅ Planning how to pay down one register item, or one module everyone dreads changing
- ✅ Breaking up a god class, a giant function or a tangled package without a rewrite
- ✅ Replacing an internal dependency or a vendor client used from many call sites while features keep shipping
- ✅ Making the case that a refactor can be done in small, stoppable steps instead of a quarter-long branch

## When NOT to use this skill

- ❌ Listing or ranking the debt in the first place — `tech-debt-register`
- ❌ Moving data, changing a schema or switching platforms with a backfill — `migration-plan`
- ❌ Writing the code for one of the steps — `feature-implement-loop`
- ❌ Deciding the target architecture or recording why — `adr-generator` or `design-doc`
- ❌ Reviewing a refactor PR that already exists — `pre-merge-review`
- ❌ Splitting a feature into user stories — `user-story-splitter`

## Anti-patterns to avoid

- ❌ **The unrequested report.** Twelve thousand characters of tables in reply to "how do we do this??". The asker wanted the sequence and the first move.
- ❌ **Same code, more files.** A plan that only moves code unchanged when the goal was "add a zone without fear". Seven helpers that each still hard-code the rules haven't made the next zone easier.
- ❌ **Tests after the open PR.** Deferring characterisation tests until a feature PR merges, so the area with the incidents stays unpinned through the riskiest weeks.
- ❌ **Quietly changing a contract.** Making a function pure, or making `send` honestly return `false`, without moving the callers that relied on the old behaviour first.
- ❌ **Deleting the module and calling it done** while a script or report still carries its own copy.
- ❌ **The rewrite in disguise.** "Step 1: build the new OrderService. Step 2: switch over."
- ❌ **Fixing bugs mid-refactor.** The first unlabelled behaviour change makes every later test failure ambiguous.
- ❌ **No stop point,** or a target nobody measured. "Easier to change" ends never.
- ❌ **Claiming a file couldn't be read** without having opened it.

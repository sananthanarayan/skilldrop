# Refactor-plan template

Two shapes. Use the chat shape unless the user asked for a document (a file, "a proper plan",
something to take to a meeting) or the plan runs past about ten steps. Never send both at
full length: when a document is written, the reply is its lead, the findings and the path.

## Chat shape (default)

```markdown
{Approach in one sentence: the technique and the end state the goal needs.}
First step: {the step} — {why it goes first}.

**What the code shows**
- `{file}:{function}` {a caller contract, a lying return value, a copy outside the module, real test coverage, a stale signal}
- … (three to six bullets, each one that changes the plan)

**Steps** (each one PR to main; you can stop after any of them)
1. [refactor] Characterisation tests for {riskiest behaviour first: …}, in {new test file}. {why}
2. [refactor] {change} — {why}. {clash or rollback, if it matters}
3. [behaviour change] {change the goal needs} — after step {n} makes it safe; {caller moved first}; rollback: {flag off / revert}.
…
n. {contract: delete the old path; add a check so it can't come back}

**Target:** {metric}: {baseline from the files, or "to measure"} → {goal}. **Stop point:** {checkable state}.
**Not touched:** {fence, one line}. Anything found during the work that isn't a step goes to the debt register.
**To confirm:** {at most three questions or checks to run}
```

## Document shape (asked for, or large)

```markdown
# Refactor plan: {the debt, in one line — "split OrderService so order features stop editing one file"}

{Approach in one sentence.} **First step:** {step} — first because {the work it unblocks}.

**Goal:** {the user's words} → **End state:** {the structure that goal needs}
**Target:** {metric}: {baseline from the input, or "not measured; step 0 measures it"} → {goal}
**Stop point:** {the "done enough" line, checkable — and what stays as it is after it}
**Not touched:** {modules, contracts, behaviours outside the fence}
[assumption] {anything inferred; one line each}

## What the code shows

- `{file}:{function}` — {finding, and the step it shapes}

## Steps

| # | Change | Type | Technique (why) | Verified by | Rollback (live side) | Risk | Size | Owner |
|---|---|---|---|---|---|---|---|---|
| 1 | Characterisation tests for {incident-prone behaviour first} in {new test file} | refactor | characterisation tests | pass on current code | revert PR | none, tests only | S | {role} |
| 2 | Move {function} to {file} unchanged; old name re-exports | refactor | move | step 1 tests + suite | revert PR | import cycles | S | {role} |
| 3 | Route {callers} through {interface} | refactor | branch by abstraction | step 1 tests | revert PR; old impl live | missed call site | M | {role} |
| 4 | {behaviour the goal needs} behind flag `{name}` | behaviour change | {technique} | updated pins, reviewed | flag off; old side live | {what} | M | {role} |
| … | | | | | | | | |
| n | Contract: delete {old path}; add {CI check} | refactor | parallel change (contract) | suite + check green | revert PR | caller outside the repo | S | {role} |

Stop after any step: each leaves the code better than before. Two paths exist from step {x}
to step {y}; nowhere else.

## Characterisation tests

| Function | Pin (riskiest first) | Includes current bug? | Lives in |
|---|---|---|---|
| `{file}:{function}` | {inputs → outputs, edge cases} | {yes: "{bug}", pinned as-is / no} | {new test file if an open PR edits the existing one} |

## Clashes with feature work

| In-flight work | Shared `file:function` | Decision | Effect on the plan |
|---|---|---|---|
| {PR or feature} | {…} | land first / wait / fold in / through the seam / freeze window | {…} |

## Scope fence

- **Not touched:** {list}
- **Pulled out of this plan:** {behaviour changes the goal doesn't need, and where each goes instead}
- **Copies outside the module:** {in or out, by name; if out, the plan doesn't claim them fixed}
- **Rule:** anything found during the work that isn't in a step goes to the debt register as a new item, not into this plan.

## To confirm

- {the facts the plan needs and the input didn't give, as checks to run}
```

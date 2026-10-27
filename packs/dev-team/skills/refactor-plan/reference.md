# Refactoring techniques: when each fits and what rollback means

**Refactor or behaviour change.** A refactor step keeps output identical and is proven by the
pinned tests passing unchanged. A behaviour change step changes a pinned value on purpose,
says which, and has its own rollback (usually a flag). A plan names the type of every step and
never puts both in one PR.

Every technique here keeps main releasable between PRs. Pick the smallest one that fits the
step; a heavier technique than the step needs adds seams nobody removes.

## Characterisation tests

**Fits:** code with no tests on the paths callers use, before any step touches it.
(Michael Feathers, *Working Effectively with Legacy Code*.)

**Step shape:** one PR that adds tests only. No production code changes, except a seam
needed to make the code testable (an injected clock, a parameter for a hard-wired client),
and that seam goes in its own PR first.

**What to pin:**
- The outputs for the inputs callers actually send — read the callers, not the docstring.
- Boundary inputs: empty, zero, negative, very large, null, duplicate, unsorted.
- Rounding, ordering, timezone and locale behaviour.
- Error behaviour: which exception, which error code, what was half-written before it raised.
- Known bugs, as they behave today. Name the test for what it is
  (`test_tax_rounds_per_line_current_behaviour`) and point it at the register item that
  records the bug.

**When output is too wide to assert by hand:** an approval (golden-master) test. Record
outputs for a set of real-shape inputs, store them next to the test, and diff on every run.
Scrub timestamps and ids first or the test flaps.

**Rollback:** revert the PR. Nothing in production changed.

**Open PRs on the same file:** never a reason to wait. The tests touch no production code, so
they go in a new test file and merge now. If the open PR changes pinned behaviour on purpose,
its author updates the pinned value in that PR, which makes the change visible in review.
**Order:** the behaviour behind past incidents and the branches comments warn about first,
the quiet paths last.

**Failure mode:** asserting what the code should do. The test fails against the current code
and the team deletes it.

## Extract / inline / move

**Fits:** a cohesive piece (a function, a group of methods sharing state) that can leave its
current home in one PR without changing callers.

**Step shape:** two PRs when the code moves files. PR A moves it unchanged and leaves the old
name pointing at the new one (re-export, delegating method). PR B changes it. Callers move
to the new name in later PRs or in the contract step.

**Rollback:** revert the PR. A pure move reverts cleanly.

**Failure mode:** move and edit in one PR. The reviewer can't see the edit in a 900-line diff.

## Branch by abstraction

**Fits:** replacing a dependency (a client, a store, a library) that many callers use, when
the swap takes more than one PR. (Paul Hammant; Martin Fowler's write-up.)

**Step shape:**
1. Introduce an abstraction over the current dependency; route callers through it in
   batches. Behaviour unchanged.
2. Build the new implementation behind the same abstraction, dark.
3. Switch which implementation is live with a flag or config, for a slice first.
4. Remove the old implementation and, if it adds nothing, the abstraction.

**Rollback:** before step 3, revert the PR. From step 3, flip the flag back — the plan names
the flag and which side is live after each step.

**Failure mode:** stopping after step 3. Two implementations stay forever.

## Parallel change (expand–contract) at code level

**Fits:** changing a function signature, an interface or a data shape that many callers
use. (Danilo Sato's write-up of the pattern on Martin Fowler's site.)

**Step shape:**
1. **Expand** — add the new signature alongside the old; the old delegates to the new.
2. **Migrate** — move callers in batches, one PR per batch.
3. **Contract** — remove the old signature once nothing calls it, and add a check (lint
   rule, test, grep in CI) that stops it coming back.

**Rollback:** each batch reverts on its own. The old signature stays live until contract.

**Failure mode:** no contract step. Schedule it within two steps of the last migrate batch.

**Caller contracts:** the same shape removes a side effect a caller relies on (a mutated
argument, a swallowed error reported as success). Expand: give the caller what it reads
another way. Migrate: move that caller. Contract: remove the side effect. Removing it is a
behaviour change and gets its own step; it is never folded into an extract.

This is the code-level version. When the change crosses a datastore with a backfill, it is a
migration, not a refactor, and it gets its own migration plan.

## Strangler fig

**Fits:** replacing a whole module or service piece by piece, when there is an edge (a
router, a facade, an entry function) where each call can go to old or new. (Martin Fowler.)

**Step shape:**
1. Put a facade at the edge; everything still goes to the old code.
2. Move one capability at a time to new code; the facade routes that capability to it.
3. When the old code serves nothing, delete it.

**Rollback:** route the capability back to the old code at the facade. The plan names, per
step, which capabilities the new code serves.

**Failure mode:** using it for something one extract would do. A facade over a single
function is a seam nobody needs.

## Mikado method

**Fits:** tangled dependencies where each attempted change breaks on something that must
change first, and nobody knows the full list. (Ola Ellnestam and Daniel Brolund, *The Mikado
Method*.)

**Step shape:**
1. Write the goal at the top of a graph ("`billing` imports nothing from `web`").
2. Try it naively. Note every breakage as a prerequisite node. **Revert.**
3. Repeat for each prerequisite until reaching leaves that change cleanly.
4. Ship the leaves first, one PR each, working back up to the goal.

**Rollback:** each leaf is one PR; revert it. The exploration commits are never merged.

**Failure mode:** keeping the naive attempt and fixing forward. That is the big-bang rewrite
arrived at by accident.

When an import graph or a compiler error list is already in the input, the first pass of the
graph comes from it: each forbidden edge is a node, and edges with no further dependency are
the leaves.

## Measuring the target

Pick one metric, two at most, and take the baseline before step 1.

| Metric | Read it from |
|---|---|
| Share of feature PRs touching the file | git log over merged PRs in a window |
| Files touched per typical change | git log for the last N changes in the area |
| Change lead time for the module | PR open to merge for PRs touching it |
| Review time for PRs touching it | the code host's PR data |
| Test run time for the module's suite | CI timings |
| Defects or incidents traced to it | the incident log or bug tracker |
| Forbidden imports or direct call sites | a grep or import-linter count, enforced in CI at the end |

A count that can be enforced in CI (forbidden imports, direct call sites) makes the best stop
point: the last step turns the count into a check, so the debt can't come back.

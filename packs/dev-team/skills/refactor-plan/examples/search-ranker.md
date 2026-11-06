# Worked example — search ranker with a flag pile

## Input given to the skill

> TD-07 from our register got the go-ahead. `search/ranker.py` has one 600-line function,
> `rank(query, docs, **flags)`, driven by 14 boolean flags listed in `RANK_FLAGS` at the top
> of the file. Register row: "5 of the last 8 search PRs changed `rank()`; INC-540 (Jul,
> `legacy_tiebreak` reversed the order of equal scores) and INC-552 (Aug, `personalise` is
> ignored when `boost_recent` is on — not fixed; the web client sends `personalise` only
> when `boost_recent` is off)." `tests/search/test_ranker.py` covers 4 of the 14 flags. PR
> #212 "Add `boost_local` flag" is open and edits `rank()`. Next quarter the mobile app needs
> its own ranking with different weights. Owner: Search team.

---

## Reply in chat (the default: the user asked how, not for a document)

Turn each flag into its own scoring function and build a ranking from a list of them, so the
mobile ranking is a new list rather than an edit to `rank()`. First step: approval tests for
every flag in a new test file, this week, because `rank()` has tests for only 4 of 14 flags.

**What the code shows**
- `search/ranker.py:rank` reads all 14 `RANK_FLAGS` in one body; `tests/search/test_ranker.py` covers 4 of them.
- INC-552 is live behaviour a client depends on: the web client sends `personalise` only when `boost_recent` is off, so the test pins it as-is.
- #212 is editing `rank()` now; moves wait for it, tests don't.

**Steps** (each one PR to main; you can stop after any of them)
1. [refactor] Approval tests in `tests/search/test_ranker_characterisation.py`: `personalise` + `boost_recent` together (INC-552, as-is), `legacy_tiebreak` on equal scores (INC-540), then each flag alone.
2. [refactor] After #212 merges: extract the tie-break block into `_tiebreak`, unchanged; it caused INC-540.
3. [refactor] Add `rank_with_profile(query, docs, profile)`; `rank(**flags)` builds a profile and delegates. The mobile team can start from here.
4. [refactor] Move the 15 flags (with `boost_local`) into scoring functions, five per PR, three PRs.
5. [refactor] Move callers to `rank_with_profile`, delete `**flags`, add a CI check that forbids new flags.

**Target:** search PRs that edit `rank()`, 5 of the last 8 → the mobile ranking ships without editing it. **Stop point:** every flag is a scoring function (step 4); step 5 is scheduled but optional.
**Not touched:** INC-552 behaviour, `RANK_FLAGS` names, weights, the API response. Anything found during the work that isn't a step goes to the debt register.
**To confirm:** does anything outside this repo call `rank()` with flags? It decides whether step 5 deletes `**flags` or keeps a shim.

---

## The same plan as a document (when the user asks for one)

# Refactor plan: take the scoring rules out of `rank()` so new rankings stop editing it

**Target:** search PRs that edit `rank()` — baseline 5 of the last 8 (TD-07) → the mobile
ranking ships without editing `rank()`.
**Stop point:** every flag in `RANK_FLAGS` is its own scoring function, and a ranking is
built from a list of them. Removing `**flags` from `rank()` is scheduled but outside the stop
point (step 7).
**First step:** characterisation tests for all 14 flags, then the expand step for a
profile-based `rank` — first because the mobile ranking next quarter is the work this
unblocks.
**Type:** every step is a refactor; ranking output is identical throughout. The mobile
weights are feature work built on step 3.
**Not touched:** INC-552 behaviour, `RANK_FLAGS` names, the search API response shape.
[assumption] `rank()` is called only from inside this repo; see To confirm.

## Steps

| # | Change | Technique | Verified by | Rollback (live side) | Risk | Size | Owner |
|---|---|---|---|---|---|---|---|
| 1 | Approval tests in a new `tests/search/test_ranker_characterisation.py`: `personalise` + `boost_recent` together, `legacy_tiebreak` on equal scores, then each flag alone | characterisation tests | new tests pass on current code | revert PR | none, tests only | M | Search team |
| — | **Wait for #212 to merge** | — | — | — | — | — | — |
| 2 | Extract the tie-break block into `_tiebreak(docs, legacy)` in `ranker.py`, unchanged | extract | step 1 tests | revert PR | ordering of equal scores (INC-540) | S | Search team |
| 3 | Add `rank_with_profile(query, docs, profile)`; `rank(**flags)` builds a profile from the flags and delegates | parallel change (expand) | step 1 tests; `rank` output identical | revert PR; `rank` is the only caller | flag-to-profile mapping misses a flag | M | Search team |
| 4–6 | Move flags into scoring functions, five, five and five per PR (15 with `boost_local`) | extract, behind step 3 | step 1 tests + #212's tests | revert that batch's PR | interaction between flags in one batch | M each | Search team |
| 7 | Move callers to `rank_with_profile`; delete `**flags`; CI check forbids new flags | parallel change (contract) | suite + check | revert PR | caller outside the repo | S | Search team |

Stop after any step: each leaves `rank()` shorter and better tested. Two entry points exist
from step 3 to step 7 and nowhere else; step 7 is scheduled for the sprint after step 6.

## Step detail (step 3 shown)

- **Change:** new `rank_with_profile` in `search/ranker.py`; `rank` keeps its signature and builds a profile from `**flags`.
- **Technique:** parallel change — callers move over later, so the old entry point stays live.
- **Verified by:** every step 1 approval test, run through `rank` (unchanged callers).
- **Rollback:** revert the PR; nothing calls `rank_with_profile` yet.
- **Risk:** a flag dropped from the profile mapping changes ranking silently; the per-flag approval tests catch it.
- **Size:** M. **Owner:** Search team.
- **Clashes:** none once #212 has merged.

## Characterisation tests

| Function | Pin | Includes current bug? | Lives in |
|---|---|---|---|
| `rank` | each of the 14 flags alone over a recorded query set | no | `tests/search/test_ranker_characterisation.py` (new, so it can't conflict with #212) |
| `rank` | equal scores with `legacy_tiebreak` on and off | no (INC-540 is fixed) | same |
| `rank` | `personalise` + `boost_recent` together | **yes: personalise ignored, pinned as-is (INC-552)** | same |

## Clashes with feature work

| In-flight work | Shared files / functions | Decision | Effect on the plan |
|---|---|---|---|
| #212 Add `boost_local` | `search/ranker.py::rank` | wait | step 2 starts after #212 merges; `boost_local` joins batch 4–6 |
| Mobile ranking (next quarter) | `rank` | fold in | the mobile team builds its profile on `rank_with_profile` once step 6 lands |

## Scope fence

- **Not touched:** search API response shape, `RANK_FLAGS` names, weights.
- **Pulled out of this plan:** fixing INC-552 is a behaviour change; it is a separate ticket, and the web client workaround has to be removed in the same change.
- **Rule:** anything found during the work that isn't in a step goes to the debt register as a new item, not into this plan.

## To confirm

- Does anything outside this repo call `rank()` with flags? It decides whether step 7 can delete `**flags` or must keep a shim.

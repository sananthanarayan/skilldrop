# Test plan template

Sections in the order a reviewer reads them: what's at stake first, cases later. Keep every section; an empty one gets a stated reason, not deletion.

```markdown
# Test plan: {feature / PR / release name}

**Source:** {story ID, PR link, or brief}
**Date:** {YYYY-MM-DD}
[assumption] {any defaults picked; omit if none}

## Coverage gaps found in the input

{ACs with no testable behavior, contradictions, missing error specs — or "none".}

## Scope

**In scope:** {surfaces this plan covers}
**Out of scope:** {touched-adjacent areas deliberately excluded} → see "Not tested"

## Risk table

| Area | What could go wrong | Likelihood | Impact | Priority |
|---|---|---|---|---|
| {surface} | {failure mode, specific} | H/M/L | H/M/L | P1/P2/P3 |

## Acceptance-criteria coverage

| AC | Test case(s) | Level |
|---|---|---|
| AC1 {short text} | TC-1, TC-4 | unit / integration / e2e |
| AC2 `[derived]` {…} | TC-2 | … |

## Test cases

### Unit

- **TC-1 (P1)** — {name}
  - Given {…} When {…} Then {concrete expected result}

### Integration

- **TC-4 (P1)** — {name}
  - Setup: {fixture / contract state}
  - Steps: {…}
  - Expected: {observable result, exact codes/values}

### End-to-end

- **TC-7 (P1)** — {journey name}
  - Why e2e: {the cross-system failure no lower level catches}
  - Steps / Expected: {…}

### Exploratory charters (P2/P3)

- **CH-1** — Explore {area} for {risk}; timebox {30–60 min}; note anything where {tripwire}.

## Test data

| Need | Detail |
|---|---|
| {record/state} | {exact shape, volume, how created or seeded} |

## Environment & flags

{Env, feature-flag states, third-party sandbox/stub mode.}

## Entry criteria

- {observable precondition}

## Exit criteria

- All P1 cases pass.
- {defect threshold, e.g. "no open major+ defects in touched areas"}
- {anything else a release manager can verdict without interpretation}

## Not tested — accepted risks

| Skipped | Why acceptable |
|---|---|
| {area or taxonomy item} | {one line: low likelihood/impact, covered elsewhere, or cost > risk} |
```

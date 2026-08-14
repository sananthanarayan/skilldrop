# Bug-ticket template

Every claim carries a tag: `[reported]` (the reporter says so), `[verified]` (confirmed by log/screenshot/own repro), `[assumption]` (triager's default). Untagged statements are the anti-pattern.

```markdown
# {Symptom + condition — searchable: "Checkout button stays disabled after removing expired coupon (Safari 17, guest cart)"}

**Severity:** S{1–4} — {one line: worst plausible user impact}
**Priority:** P{1–3} — {one line: business urgency, judged separately}
**Blast radius:** {all users | segment | one tenant} `[reported|verified|assumption]`
**Component (best guess):** {area} `[assumption]`

## Summary

{2–3 sentences: who hits it, doing what, with what result. No cause claims.}

## Environment

| Field | Value | Tag |
|---|---|---|
| App version / commit | … | `[verified]` |
| OS / browser / device | … | `[reported]` |
| Account / tenant type | … | `[reported]` |
| First seen / last worked | … | `[reported]` |

## Reproduction

{Pick exactly one of the two blocks:}

**Steps (from clean state):**
1. {fresh session, named test account, starting URL}
2. {observable action}
3. {observable action → failure}
**Reproduces:** {n/n attempts} `[verified]`

**— or — No repro yet.** Collect:
- Verbatim error text / screenshot of the exact moment
- Console or server logs for {window} around {timestamp}
- HAR capture / request ID of the failing call
- Screen recording if UI-state dependent

## Expected vs actual

**Expected:** {concrete, one line}
**Actual:** {concrete, one line}
**Error (verbatim):** `{exact string, or "none shown"}`

## Hypotheses (≤3 — each with a 5-minute check; none of these is a conclusion)

| # | Hypothesis | Quick check |
|---|---|---|
| H1 | … | … |

## Questions for reporter (≤3, ranked by diagnostic value)

1. …

## Duplicate-search hints

`{error code}` · `{symptom phrase}` · `{component + verb}`

## Split out (if the report contained more than one issue)

- {symptom} → {new ticket ref / to be filed}
```

## Severity / priority matrix

**Severity — worst plausible user impact (not who reported it):**

| | Definition | Examples |
|---|---|---|
| S1 | Data loss, security exposure, payments broken | double-charge; cross-tenant read; corrupted saves |
| S2 | Core flow broken, no workaround | can't log in; checkout dead-ends |
| S3 | Degraded, workaround exists | export fails but copy-paste works; retry succeeds |
| S4 | Cosmetic / minor friction | misalignment; typo; flicker |

**Priority — business urgency (judged independently):**

| | Definition |
|---|---|
| P1 | Drop current work; fix and ship now |
| P2 | This sprint |
| P3 | Backlog, batch with related work |

Legitimate mismatches prove the separation: S4/P1 (typo in the price during launch week), S2/P3 (core flow of a feature being sunset next month).

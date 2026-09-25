---
name: bug-triage
description: Turn a vague bug report (Slack message, support ticket, "it's broken on mobile sometimes") into an actionable ticket — searchable symptom title, numbered repro steps from a clean state, expected vs actual, severity separated from priority, evidence tagged reported-vs-verified, and labeled hypotheses instead of root-cause guesses. Use when the user wants to triage a bug, write up a bug report, turn a complaint into a ticket, or make a flaky issue actionable.
---

# bug-triage

Converts the bug report someone *sent* into the ticket an engineer can *start* — without a round of "can you clarify?" first. The discipline: separate what was reported from what's verified, separate severity from priority, and label every guess as a guess. Triage shapes the work; fixing it is `feature-implement-loop` (or a human) downstream.

## How to respond

1. **Ingest the raw report** — Slack thread, support ticket, user email, a teammate's "X is broken". Mine it for the six ticket fields before asking anything. Then ask **at most 3 questions, ranked by diagnostic value** — the answers that most shrink the search space (exact error text, when it last worked, does it reproduce on a second account/device). Everything unconfirmed proceeds with a tag, not a guess.

2. **One bug per ticket.** A report with three symptoms becomes three tickets (or one ticket + a "split out" note naming the others). Multi-symptom tickets close half-fixed.

3. **Write the title as symptom + condition, searchable.** ✅ *"Checkout button stays disabled after removing an expired coupon (Safari 17, guest cart)"* — ❌ *"Checkout broken"*, ❌ *"Coupon bug"*. Six months from now someone greps tickets for "disabled checkout" — that's who the title is for.

4. **Tag every claim `[reported]` or `[verified]`.** What the reporter says happened vs what was confirmed by logs, a screenshot, or your own reproduction. Triage that presents `[reported]` as fact sends an engineer chasing a description instead of a behavior.

5. **Number the repro steps from a clean state** — fresh session, named test account, stated starting URL — each step an observable action, ending in the failure. If reproduction is unknown, the ticket says **"No repro yet"** and lists the exact diagnostics to collect (error text verbatim, console/server log window with timestamp, HAR capture, screen recording) — never invented steps that "probably" trigger it.

6. **Split expected vs actual into two concrete lines.** ✅ Expected: *"order total recalculates to pre-coupon price"* / Actual: *"total keeps the discount, button stays disabled"* — ❌ *"it doesn't work right"*. Attach the verbatim error message if one exists; paraphrased errors are unsearchable.

7. **Call severity and priority separately** with one line of reasoning each, using the matrix in [`templates/bug-ticket.md`](templates/bug-ticket.md):
   - **Severity** = worst plausible user impact: S1 data loss / security / payment broken · S2 core flow broken, no workaround · S3 degraded, workaround exists · S4 cosmetic
   - **Priority** = business urgency: P1 drop everything · P2 this sprint · P3 backlog
   A cosmetic bug on the pricing page during launch week is S4/P1 — the separation is the point. State the blast radius guess: who's affected (`all users` / `Safari only` / `one tenant`) and tag it.

8. **Offer hypotheses as hypotheses.** Up to 3, each with a 5-minute check that would confirm or kill it. ✅ *"H1: expired-coupon validation leaves cart state locked — check: apply/remove a valid coupon, see if button recovers"*. Never present the leading hypothesis as the cause; that anchors the investigation on a guess.

9. **Finish with duplicate-search hints** — 2–3 search strings for the tracker (error code, symptom phrasing, component name) so the ticket isn't the third copy.

## Useful references in this skill

- [`templates/bug-ticket.md`](templates/bug-ticket.md) — the ticket skeleton with the severity/priority matrix and the no-repro diagnostics list

## Quality bar

- **An engineer can start without contacting the reporter.** Either the repro stands alone or the no-repro diagnostics list says exactly what to collect.
- **Title findable by symptom search.** If the words a future reporter would type don't appear in it, retitle.
- **Zero untagged claims.** Every factual statement is `[reported]`, `[verified]`, or `[assumption]` — a triager's authority comes from the tags.
- **Severity and priority each have a stated reason**, and they were judged independently — one line each, no shared justification.
- **Hypotheses ≤ 3, each with a concrete check.** A hypothesis without a check is a vibe.
- **The verbatim error text is present** when any error was shown — quoted exactly, not paraphrased.

## When to use this skill

- ✅ A Slack/support complaint needs to become a ticket an engineer can pick up
- ✅ "Can you write this up properly?" for a vaguely described bug
- ✅ Triaging an inbound bug queue into severity/priority order
- ✅ A flaky, "sometimes" bug that needs a diagnostics plan instead of guesswork

## When NOT to use this skill

- ❌ Actually fixing the bug — hand the ticket to `feature-implement-loop` or a human
- ❌ A production incident in progress — mitigate first; this is queue work, not response work
- ❌ The post-incident analysis — that's `postmortem-generator`
- ❌ A feature request wearing a bug costume ("bug: there's no dark mode") — route to `user-story-splitter`

## Anti-patterns to avoid

- ❌ **Root-cause cosplay.** "It's probably the cache" stated as fact in the ticket body — now the investigation starts at the guess instead of the evidence.
- ❌ **Repro steps that skip state.** "1. Go to checkout 2. See bug" — which account, which cart, which browser? Steps that don't start clean don't reproduce.
- ❌ **Severity inflated to get attention** (everything S1) or priority used as severity (P1 because a VP reported it — that's priority, write it as priority).
- ❌ **The interrogation.** Ten questions back to the reporter before writing anything; three ranked ones, then proceed with tags.
- ❌ **Paraphrased error messages.** "Some kind of permissions error" when the dialog said `ERR_TENANT_SCOPE_403` — the exact string is the most diagnostic fact available.
- ❌ **The kitchen-sink ticket.** Three symptoms, two feature requests, and a screenshot dump under one title. Split it.

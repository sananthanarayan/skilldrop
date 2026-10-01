---
name: incident-comms
description: Draft audience-segmented updates during a live incident — customer status-page posts, internal stakeholder updates, and exec notifications — each leading with user-facing impact, never speculative cause or ETA, always naming the next-update time. Use when an incident is in progress and the user needs a status page post, customer notification, internal update, exec brief, or the resolved/all-clear message.
---

# incident-comms

Produces the words you send *while the incident is still burning* — when the runbook says how to fix it and `postmortem-generator` comes after. The discipline: impact before cause, committed cadence before content, and never a claim you'd have to walk back. A walked-back update costs more trust than the silence it replaced.

## How to respond

1. **Get the three facts that gate every message.** Before drafting: **who's affected and how** (in their terms, not yours), **what's confirmed vs suspected**, and **when the next update goes out**. Ask at most 2 questions, spent on impact scope and confirmed-vs-suspected — the cadence you can set yourself. If impact is still unknown, that *is* the message ("we're investigating reports of…"), not a reason to wait.

2. **Pick the lifecycle stage** — the stage dictates structure (templates in [`templates/`](templates/)):
   - **Acknowledge** — fastest possible "we know, we're on it, next update at HH:MM". Speed beats completeness; a 3-line ack in 5 minutes beats a perfect paragraph in 30.
   - **Update** — what changed since last time, what's being done now, revised next-update time. Sent on the cadence *you committed to* whether or not there's news ("no change yet, still investigating, next update HH:MM" is a valid and trust-preserving update).
   - **Resolve** — what's restored, from when, what to do if still affected, and that a postmortem will follow (for SEV1/2).

3. **Segment by audience — three messages, not one forwarded three times.** Same facts, different altitude (full guidance in [`reference.md`](reference.md)):
   - **Customers (status page / in-app):** impact in their words, no internal jargon, no cause speculation, no name-and-blame of a vendor. ✅ *"Some users are unable to upload files. We've identified the cause and are working on a fix."*
   - **Internal stakeholders (support, sales, account teams):** the above plus what to tell *their* customers, whether to pause comms, and the workaround if one exists — they're relaying, so arm them.
   - **Execs:** business impact (revenue/customers/SLA exposure), the decision being asked of them if any, and what you need — not a technical narrative. Three sentences. They escalate or unblock; they don't debug.

4. **Lead with impact, in the reader's terms.** The first sentence says what the reader cannot do right now. ✅ *"Checkout is failing for about 20% of customers."* — ❌ *"We're seeing elevated 5xx rates from the payments service."* (the customer doesn't have a payments service; they have a checkout that's broken).

5. **Never ship a claim you might retract.** No speculative root cause ("this appears to be a database issue" — until it's confirmed, it isn't), no ETA you can't commit to ("fixed within the hour" sets a clock you'll be judged against), no all-clear before verification. Where pressure demands a time, commit only to the **next update time**, which is entirely in your control. State confidence honestly: "investigating" / "identified" / "monitoring a fix" / "resolved" — the standard status vocabulary, used precisely.

6. **Stay blameless and external-safe.** No individual named, no vendor blamed ("our upstream provider" not "AWS is down" until it's both confirmed and yours to disclose), nothing that becomes a screenshot you regret. Assume every internal message gets forwarded and every customer message gets posted to social media — write the one you'd stand behind there.

7. **Emit the requested message(s) ready to paste**, each with its channel labeled and the next-update timestamp filled or marked `[set HH:MM]`. When stage is "resolve", include the one-line handoff to `postmortem-generator`. Offer the matching internal/exec versions if the user asked for only one and the others clearly apply.

## Useful references in this skill

- [`reference.md`](reference.md) — per-audience altitude guide, the status vocabulary, and cadence-by-severity table
- [`templates/`](templates/) — paste-ready acknowledge / update / resolve messages for status page, internal, and exec channels

## Quality bar

- **First sentence is reader-facing impact**, not internal symptom. If a customer needs your architecture diagram to parse it, rewrite.
- **Every message names the next-update time** (or marks it `[set HH:MM]`). The cadence promise is the entire contract; an update with no next-time is a dead end.
- **Zero retractable claims.** No unconfirmed cause, no committed fix-ETA, no premature all-clear. The only time committed is the next update.
- **Three audiences are genuinely different**, not one text with words swapped. Exec version is business impact + ask; customer version is impact + action; internal version arms the relayer.
- **Blameless and forward-safe** — no person, no unconfirmed vendor blame, nothing you wouldn't want screenshotted.
- **Resolve messages tell still-affected users what to do** and promise the postmortem for SEV1/2.

## When to use this skill

- ✅ An incident is live and customers/stakeholders/execs need updating
- ✅ Drafting or updating a status-page post mid-incident
- ✅ The "what do we tell people?" moment during an outage
- ✅ The resolved / all-clear message and its internal + exec variants

## When NOT to use this skill

- ❌ The incident is over and you're analyzing it — that's `postmortem-generator`
- ❌ How to technically mitigate — that's the `runbook-generator` runbook
- ❌ A planned-maintenance notice (no failure, no pressure) — a normal scheduled-comms template, not this
- ❌ Pre-writing a generic incident-comms *policy* — this drafts live messages; the policy is a runbook section

## Anti-patterns to avoid

- ❌ **Cause speculation in a customer post.** "This appears to be related to a recent deploy" — now you've committed to a story you may have to unwind in public.
- ❌ **Committing to a fix ETA.** "Service will be restored by 3pm" starts a clock; miss it and the next update is an apology. Commit to the *next update time* instead.
- ❌ **Going silent between updates.** Skipping the cadence because "there's nothing new" reads as "they've lost control." Send the no-change update.
- ❌ **One message, three forwards.** Sending the engineer-language internal update straight to the status page, or the customer post to the CEO. Different readers, different altitude.
- ❌ **Naming a person or an unconfirmed vendor.** "Dave's deploy" / "AWS is down" — blame in a forwardable message is a permanent record of a guess.
- ❌ **The premature all-clear.** "Resolved" before the fix is verified across all affected paths — the second outage in one incident is the one that makes the news.
- ❌ **Jargon as reassurance.** "We've failed over to the secondary replica and are draining the queue" tells a customer nothing except that you've stopped speaking their language.

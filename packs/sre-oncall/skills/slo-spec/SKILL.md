---
name: slo-spec
description: Define service level objectives for a service from its critical user journeys — each SLI a good-events / valid-events ratio with both sides defined and measured where the user feels it, a target set from user need and history (checked against dependency SLOs), the error budget computed in minutes and bad requests at current traffic, multi-window burn-rate alerts with the budget consumed when each fires, low-traffic handling, and an error-budget policy with owners. Use when the user asks to "define SLOs", "write our SLIs", "how much error budget do we have", "what burn-rate alerts should page", "is 99.99% realistic", or "write an error-budget policy".
---

# slo-spec

Turns a service's user journeys into SLOs a team can defend: what counts as a good and a valid
event, the target and window, the budget in real units, the alerts that fire on it, and what
the team does when it's spent. This is the reliability contract. The wider set of
non-functional targets for a design is `nfr-spec`; what to instrument, log and trace and which
dashboards to build is `observability-plan`; the procedure on-call follows when an alert fires
is `runbook-generator`; DORA delivery metrics are `delivery-metrics-report`.

## How to respond

**Four rules come before the steps and outrank them:**

- **Answer what was asked, first.** Open with the answer, the decision or the artifact, in plain words. Scores, matrices, frameworks and tags come after it, and anything that doesn't change the answer is cut.
- **Use only what you were given.** Don't add facts, names, numbers, incidents, history, steps or sections the input doesn't contain. What you need and don't have is left out of the artifact and listed once at the end under "To confirm".
- **Deliver from what you have.** When the request gives you something to work on, state your assumptions in a line and produce the result. When it gives you nothing to work on, ask for it in one or two plain sentences and say what you will do once you have it.
- **Write for someone who has never heard of this skill.** No skill names, no paths or scripts from this folder, no internal terms, and nothing about how the run was set up. A next step is one plain sentence at the end that describes the work.
- **For this skill:** Every budget, threshold and alert number is computed, never estimated, and shown in real units (minutes, bad requests). A target that can't be met — above a dependency's SLO, or measured where it can't see the user's wait — is said in the first lines, not in a footnote.

1. **Start from 2–4 critical user journeys, not from the metrics that exist.** A journey is
   something a user does and would complain about losing: ✅ *"place an order and see it
   confirmed"* — ❌ *"order-worker latency"*, ❌ *"CPU < 80%"*. Rank by what an outage costs the
   user. Everything past four is a dashboard, not an SLO. An internal or staff-only journey
   still counts if people depend on it, but gets its own target and alerting (step 6).

2. **Write each SLI as good events / valid events, with both sides defined.** Name the
   request set, what makes one *valid*, and what makes one *good*:
   - ✅ *"Valid: `POST /bookings` from customers, excluding 4xx validation errors and synthetic
     test bookings. Good: reaches 'confirmed' or 'declined by bank' within 20 s of the request
     arriving at the load balancer."*
   - ❌ *"Checkout availability: 99.9%"* — of what? A card decline is a correct outcome, not a
     failure; a 429 we caused is a failure, not an exclusion.
   Latency SLIs are a threshold count (✅ *"% of searches answered in < 800 ms"*), never an
   average or "p99 = X". An asynchronous journey is good only when the user sees the outcome,
   so the SLI spans submit → result, not the accepting `202`.

3. **Measure as close to the user as possible.** Prefer, in order: client / real-user beacon,
   load balancer or edge, then the app. Reject a timer that can't see queueing:
   ✅ *"from LB request timestamp to the confirmation event"* — ❌ *"worker process time"* when
   orders wait in a queue first (the worker shows 200 ms while customers wait 90 s). If
   the input shows a measured SLI disagreeing with what users reported, that is the finding:
   lead with it. Name what the chosen point still misses (client-side failures for an LB SLI).

4. **Set targets from what users need and from history — never 100%, never five nines by
   default.** Start at or slightly below what the journey achieved over the last 1–3 months
   when users weren't complaining; tighten only with a reason. History measured at the wrong
   point (the accepting response, not the outcome) overstates the journey: say so and mark the
   target provisional until a month of the new SLI exists. Check every hard dependency the journey calls
   synchronously: a target above the product of their SLOs is **not achievable without
   redundancy** (a second provider, a cache, a queue-and-retry fallback) — say so and name the
   redundancy it would take. ✅ *"99.99% isn't reachable while every booking needs the card
   processor at 99.9%; the processor alone would spend 10× the budget."* — ❌ quietly writing
   99.99%. A target equal to a dependency's SLO leaves nothing for the service's own failures; flag that too.
   Default window: 30 days rolling `[assumption]` unless the team reviews on another cadence.

5. **Compute the error budget in real units — run the script, don't estimate.**

   ```bash
   # Claude Code
   python3 "${CLAUDE_SKILL_DIR}/scripts/slo_math.py" --target 99.9 --window 30 --rpd 1000000 --dep 99.95
   # Other IDEs (from the skill folder)
   python3 scripts/slo_math.py --target 99.9 --window 30 --rpd 1000000 --dep 99.95
   # Price a past outage against the budget: --outage 40 (minutes, repeatable)
   # Several SLOs at once: a JSON list (shape in the script header), or - for stdin
   python3 scripts/slo_math.py --batch slos.json --json
   ```

   It prints the budget as minutes of full outage and as bad requests per window at the given
   traffic, the alert table, the dependency ceiling, the share a given outage spends, and
   flags. ✅ *"99.9% over 30 days = 43.2
   minutes, or 30,000 failed requests at 1,000,000 a day."* — ❌ *"about 40 minutes a month."* Use
   average traffic and say so; peak hours burn budget faster than the minutes suggest. If no
   script can run, do the arithmetic in the reply and show it (formulas in
   [`reference.md`](reference.md)).

6. **Alert on burn rate, not on raw error rate.** Default to the multi-window, multi-burn-rate
   set: 14.4× over 1 h with a 5 m short window → page (2% of a 30-day budget gone); 6× over 6 h
   with 30 m → page (5%); 1× over 3 d with 6 h → ticket (10%). Both windows must breach. Every
   row states the error rate that trips it, the budget consumed when it fires and the time to
   exhaustion, from the script. ❌ *"Page if error rate > 1% for 5 minutes"* — it pages on a blip
   that costs 0.1% of the budget and stays quiet through a slow burn that spends all of it.
   If the window isn't 30 days, keep the burn rates and report the consumed share the script
   gives; don't pretend 14.4× still means exactly 2%.

7. **Low-traffic journeys: say the ratio is noisy, then change the method.** When the script
   flags a window with fewer than ~10 expected bad events, an alert there fires on two
   failures. Pick one and say why: a longer SLO window (90 days), longer alert windows, a
   synthetic probe at a fixed rate that sets the event count, or ticket-only alerting in the
   hours people use it. ✅ *"Back-office API: 800 requests/day gives 0.48 bad requests in the 1 h
   window — a page would fire on one error. Ticket on 3 failures in 6 h during office hours
   and add a probe every minute."* — ❌ copying the paging set from the busy journeys.

8. **Write the error-budget policy with owners, agreed in advance.** It says what changes at
   each budget level and who decides: ✅ *"Budget spent: release freeze except fixes and
   security patches; the next sprint's top item is the largest budget consumer; owner — the
   team's engineering lead; exception — the head of engineering signs a written exception."*
   Include: thresholds (e.g. 50% spent in the first half of the window → reliability work
   jumps the queue; 100% → freeze), what's exempt, what happens when a dependency spent the
   budget (escalate to its owner; the freeze still covers risky changes), and when it's
   reviewed. Owners are roles or names from the input; never invent a person.

9. **Write it up with [`templates/slo-spec.md`](templates/slo-spec.md)** — the findings first
   (unachievable targets, wrong measurement point, noisy journeys), then per journey: SLI
   with good/valid definitions and measurement point, target and window, budget in minutes
   and requests, alert table, then the policy. For a chat question ("how much budget is
   99.95%?") answer in a few lines with the numbers and one alert table; no document.

**Non-interactive runs** (subagent, CI, headless): a missing window becomes 30 days rolling,
a missing target becomes one set from the stated history, and missing traffic leaves the
budget in minutes only — each tagged `[assumption]` and listed first. If the input names no
service, journey or user-facing behaviour at all, emit `BLOCKED: need the service and what its
users do with it`, because SLIs invented without journeys measure nothing.

## Useful references in this skill

- [`reference.md`](reference.md) — SLI menu by journey type, measurement points and what each misses, valid-event exclusions, budget and burn-rate formulas, dependency ceilings, low-traffic options, and a policy skeleton
- [`templates/slo-spec.md`](templates/slo-spec.md) — the write-up skeleton
- [`scripts/slo_math.py`](scripts/slo_math.py) — budget in minutes and requests, burn-rate alert table, noise and dependency flags (stdlib only, `--json`)
- [`examples/ticket-booking.md`](examples/ticket-booking.md) — worked example with real script output

## Quality bar

- **2–4 journeys, each with an SLI written as good / valid events,** both sides defined, including what's excluded from valid.
- **The measurement point is named and can see what the user waits for** — including queue time on async paths.
- **No target is 100%, none is five nines without a reason in the input,** and none sits above the hard dependencies' combined SLO without naming the redundancy it needs.
- **Every budget is in minutes and bad requests at stated traffic,** matching the script output.
- **Alerts are burn-rate rows with long and short windows,** each with the trip rate, the budget consumed at fire and the time to exhaustion.
- **Low-traffic journeys are flagged with the count that makes them noisy** and get a different method, with the reason.
- **The policy names owners, thresholds, the freeze rule, the exception route and the dependency case.**
- **Nothing in it is invented:** traffic, history, dependency SLOs and people all come from the input or are tagged `[assumption]`.

## When to use this skill

- ✅ "Define SLOs / SLIs for this service" from a description of what users do
- ✅ "How much error budget is 99.9% over 28 days at our traffic?"
- ✅ "What burn-rate alerts should page us?" or "is our error-rate alert right?"
- ✅ "Is 99.99% realistic for checkout?" — target pushback against history and dependencies
- ✅ "Write our error-budget policy"

## When NOT to use this skill

- ❌ The full set of non-functional targets for a design — latency, durability, privacy, cost — that's `nfr-spec`
- ❌ What to instrument, metrics/logs/traces split, cardinality, dashboards — that's `observability-plan`
- ❌ The step-by-step procedure when an alert fires — that's `runbook-generator`
- ❌ Deployment frequency, change fail rate, lead time — that's `delivery-metrics-report`

## Anti-patterns to avoid

- ❌ **Metrics-first SLIs.** Starting from what Prometheus already has and calling CPU, pod restarts or worker time an SLO.
- ❌ **The SLI behind the queue.** An app or worker timer that starts after the request waited, so the SLO stays green while users stare at a spinner.
- ❌ **Undefined "valid".** Counting card declines and bot traffic as failures, or dropping our own 429s and timeouts from the denominator.
- ❌ **Nines by ambition.** 99.99% because "it's revenue", on top of a provider at 99.9%.
- ❌ **"About 40 minutes".** A budget guessed, rounded, or given only as a percentage.
- ❌ **Raw error-rate paging.** "Error rate > 1% for 5 m" instead of burn rate over two windows.
- ❌ **One alert set for every journey.** Paging rules copied onto an 800-request/day API, where one failure is an incident.
- ❌ **A policy with no owner or exception route** — so the first time the budget runs out, the freeze is argued from scratch and dropped.

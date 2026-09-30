---
title: From complaint to closed incident
summary: A user complaint triggers a full response cycle — discover what's broken, operate to fix it, and close the loop with a postmortem and runbook update. Uses the discover and operate loops.
kind: tutorial
---

# From complaint to closed incident

A vague support complaint lands on a Monday morning. Two hours later the incident is understood, contained, documented, and the runbook is updated. This walkthrough shows how the `discover` and `operate` loops turn noise into a closed incident — and why they are two separate loops instead of one.

Install both loops up front:

```bash
npx skilldrop-cli install --loop discover operate
```

---

## The situation

It is 09:14 on a Monday. Three support tickets arrive in under two hours, all variations of the same complaint: checkout is failing for orders above a certain value. A Slack alert from the payment service confirms elevated 500 error rates starting at 08:47. The SRE on-call opens a session.

---

## Stage 1 — Understand (`discover` loop, G0 gate)

The `discover` loop runs first. Its job is to turn a raw signal into a requirement a human can ratify — nothing more.

### `signal-to-requirement`

Paste the three support tickets and the Slack alert into context, then invoke the skill:

```
Here are three support tickets and a monitoring alert received this morning.
Run signal-to-requirement to produce a structured incident requirement.

Ticket #8821: "My order for $620 failed at checkout with a generic error."
Ticket #8824: "Tried to buy $540 worth of items, got a 500 error on payment."
Ticket #8829: "Cart total was $890, payment page errored out immediately."
Alert: payment-service 500 error rate 4.2% (baseline 0.1%), onset 08:47 UTC.
```

The skill interviews you on ambiguities — which payment path, which environment, whether the $500 threshold is confirmed or inferred — and produces:

> **Structured requirement:**
> "Payment service returns HTTP 500 on orders exceeding $500 due to a downstream timeout in the fraud-check API. Threshold appears to be $500 but is unconfirmed. Scope: production checkout only. Onset: 08:47 UTC Monday."

### Gate G0 — human ratification

The gate asks one question: *Is this requirement specific enough for an SRE to act on, or does it need more information?*

A `READY` verdict looks like:

```
G0 READY
Requirement is actionable. Threshold is flagged as unconfirmed but the
incident is scoped and the onset is known. Proceed to operate.
```

If the requirement were too vague (e.g., "payment sometimes fails"), the gate returns `REVISE` with the specific gap. In this case it is ready. The SRE ratifies and moves to the operate loop.

---

## Stage 2 — Respond (`operate` loop)

The `operate` loop owns everything from first response to closed incident. It sequences `incident-response` → `runbook-generator` → `postmortem-generator` with a feedback edge at G3 that routes postmortem deltas back to update the living runbook.

### `incident-response`

Pass the ratified requirement as context:

```
Ratified requirement: "Payment service returns HTTP 500 on orders exceeding
$500 due to a downstream timeout in the fraud-check API."
Run incident-response.
```

The skill produces a triage plan:

- Confirm the $500 threshold by querying payment service logs for the last 3 hours
- Check fraud-check API response times against SLA (target: <200ms, current: unknown)
- Identify whether the timeout is a new regression or a latency drift
- Immediate mitigation: raise the fraud-check timeout threshold from 2s to 8s pending root cause
- Communication: draft a status page update and customer-facing message

The SRE follows the plan. Logs confirm the threshold is $500 (the fraud-check API is called only for orders above this value). The API response time has drifted from 180ms to 3.4s over the past 72 hours — a new third-party API change, not a regression in payment service code. The timeout is raised and 500 errors stop within 4 minutes.

### `runbook-generator`

With the root cause confirmed, generate a runbook for this class of incident:

```
Context: fraud-check API timeout causing payment 500s on orders >$500.
Root cause: third-party API latency drift exceeding our 2s timeout.
Mitigation: raise timeout threshold; escalate to vendor.
Run runbook-generator to produce a living runbook for this incident class.
```

The skill produces a runbook covering: detection signals, threshold confirmation steps, immediate mitigation, vendor escalation path, and verification steps to confirm recovery.

### `postmortem-generator`

After the incident is resolved, run the postmortem:

```
Incident closed at 11:03 UTC. Root cause: third-party fraud-check API
latency drift. Mitigation: timeout threshold raised from 2s to 8s.
Customer impact: ~2 hours, ~40 affected orders. Run postmortem-generator.
```

The postmortem draft covers timeline, root cause analysis, contributing factors (no alerting on third-party API latency), action items, and — critically — a **runbook delta**: a diff of what the existing runbook is missing.

### Gate G3 — postmortem closes the loop

The `operate` loop's gate reads the postmortem's runbook delta and routes it back to `runbook-generator`:

```
G3 PROCEED
Postmortem filed. Runbook delta identified: add vendor latency monitoring
to detection signals section; add vendor escalation SLA to mitigation.
Routing delta to runbook-generator for update.
```

Run `runbook-generator` again with the delta:

```
Existing runbook: [paste]. Runbook delta from postmortem: add vendor
latency monitoring to detection signals; add vendor escalation SLA (4h
response) to mitigation path. Apply and regenerate.
```

The updated runbook is committed as a PR.

---

## Stage 3 — Verify

`pre-merge-review` gates the runbook update PR before it merges to the ops repository. The three reviewers check: does the runbook accurately reflect the incident? Are the detection signals specific? Is the mitigation reversible?

Once the gate passes, the PR merges. The incident is closed:

- Support tickets resolved and customers notified
- Runbook updated with vendor monitoring and escalation path
- Postmortem filed with action items tracked
- Gate G3 confirmed the loop is closed

---

## What this shows

The `discover` and `operate` loops are separated because the cost of a mistake at each stage is different. A discovery mistake — misidentifying the requirement — costs a re-brief. An operate mistake — deploying the wrong mitigation — reaches live users. That asymmetry is why G0 is a human gate (a human ratifies the requirement) while the operate loop runs closer to the system. The boundary is not about skill quality; it is about reversibility.

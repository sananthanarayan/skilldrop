---
title: From complaint to closed incident
summary: A user complaint triggers a full response cycle — find what's broken, fix it, and close it with a postmortem and a runbook update — using the product-manager and sre-oncall skills in order.
kind: tutorial
stage: operate
---

# From complaint to closed incident

A vague support complaint lands on a Monday morning. Two hours later the incident is understood, contained, documented, and the runbook is updated. This walkthrough runs the skills for finding the problem and running the service, in order, and shows where you decide.

Both stages run as skills, with no loop. Their loops were retired: on held-out evals, the same skills used without the loop were preferred.

Install both packs up front:

```bash
npx skilldrop-cli install --pack product-manager
npx skilldrop-cli install --pack sre-oncall
```

---

## The situation

It is 09:14 on a Monday. Three support tickets arrive in under two hours, all variations of the same complaint: checkout is failing for orders above a certain value. A Slack alert from the payment service confirms elevated 500 error rates starting at 08:47. The SRE on-call opens a session.

---

## Turn the complaints into one requirement

Start with the raw signal. Paste the three support tickets and the alert, and ask for the pattern:

```
Here are three support tickets and a monitoring alert received this morning.
Run feedback-synthesis on them and give me one structured incident requirement.

Ticket #8821: "My order for $620 failed at checkout with a generic error."
Ticket #8824: "Tried to buy $540 worth of items, got a 500 error on payment."
Ticket #8829: "Cart total was $890, payment page errored out immediately."
Alert: payment-service 500 error rate 4.2% (baseline 0.1%), onset 08:47 UTC.
```

`feedback-synthesis` groups the tickets, separates what they show from what they suggest, and produces:

> **Structured requirement:**
> "Payment service returns HTTP 500 on orders exceeding $500 due to a downstream timeout in the fraud-check API. Threshold appears to be $500 but is unconfirmed. Scope: production checkout only. Onset: 08:47 UTC Monday."

You decide whether it is specific enough to act on. Here it is: the threshold is flagged as unconfirmed, but the incident is scoped and the onset is known. Had it read "payment sometimes fails", you would go back to the tickets for the missing detail before anyone touched production.

---

## Respond, document and learn

Running the service uses four skills in order: `observability-plan`, `runbook-generator`, `incident-comms` and `postmortem-generator`. This incident starts mid-way, so the first two come after the fix.

### Contain it and tell people

Pass the requirement as context and ask for the status update:

```
Requirement: "Payment service returns HTTP 500 on orders exceeding $500
due to a downstream timeout in the fraud-check API."
Run incident-comms: a status page update and a customer-facing message.
```

The SRE triages in parallel:

- Confirm the $500 threshold by querying payment service logs for the last 3 hours
- Check fraud-check API response times against SLA (target: <200ms, current: unknown)
- Identify whether the timeout is a new regression or a latency drift
- Immediate mitigation: raise the fraud-check timeout threshold from 2s to 8s pending root cause

Logs confirm the threshold is $500 (the fraud-check API is called only for orders above this value). The API response time has drifted from 180ms to 3.4s over the past 72 hours — a new third-party API change, not a regression in payment service code. The timeout is raised and 500 errors stop within 4 minutes. `incident-comms` drafts the resolved update.

### Write the runbook

With the root cause confirmed, generate a runbook for this class of incident:

```
Context: fraud-check API timeout causing payment 500s on orders >$500.
Root cause: third-party API latency drift exceeding our 2s timeout.
Mitigation: raise timeout threshold; escalate to vendor.
Run runbook-generator to produce a living runbook for this incident class.
```

The skill produces a runbook covering: detection signals, threshold confirmation steps, immediate mitigation, vendor escalation path, and verification steps to confirm recovery.

### Run the postmortem

After the incident is resolved, run the postmortem:

```
Incident closed at 11:03 UTC. Root cause: third-party fraud-check API
latency drift. Mitigation: timeout threshold raised from 2s to 8s.
Customer impact: ~2 hours, ~40 affected orders. Run postmortem-generator.
```

The postmortem draft covers timeline, root cause analysis, contributing factors (no alerting on third-party API latency), action items, and — critically — a **runbook delta**: a diff of what the existing runbook is missing.

### Feed the delta back into the runbook

You decide when the incident is closed: when the postmortem changes a procedure, not when the errors stop. Run `runbook-generator` again with the delta:

```
Existing runbook: [paste]. Runbook delta from postmortem: add vendor
latency monitoring to detection signals; add vendor escalation SLA (4h
response) to mitigation path. Apply and regenerate.
```

Then run `observability-plan` on the payment service, naming the missing vendor-latency alert, so the next drift pages someone before customers notice. The updated runbook is committed as a PR.

---

## Review the runbook change before it merges

`pre-merge-review` gates the runbook update PR before it merges to the ops repository. The three reviewers check: does the runbook accurately reflect the incident? Are the detection signals specific? Is the mitigation reversible?

Once the gate passes, the PR merges. The incident is closed:

- Support tickets resolved and customers notified
- Runbook updated with vendor monitoring and escalation path
- Postmortem filed with action items tracked
- A vendor-latency alert planned for the payment service

---

## What this shows

Finding the problem and running the service carry different costs. A mistake in the requirement costs a re-brief; a mistake in the mitigation reaches live users. Both stages are skills you run in order, and both end where you decide: whether the requirement is specific enough to act on, and whether the postmortem changed a procedure. The only automated gate in this walkthrough is `pre-merge-review` on the runbook change.

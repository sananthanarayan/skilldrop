# Rubric: Runbook

Mirrors `runbook-generator`'s quality bar — and the harshest test: would a sleep-deprived on-caller at 3am succeed using this?

## Blockers
- **Service identity is unambiguous** — name + one-line purpose. No "the service" without naming it.
- **Owner team listed (role-based, not individuals).** Individual names go stale; rotations/teams don't.
- **Escalation chain is present.** "Page primary, then secondary, then manager" with the rotation name.
- **Rollback is one command or three steps max.** If rollback is a 12-step procedure, link to a script — and that script must exist.
- **Every listed alert has a response.** A "common alerts" section that doesn't cover all alerts is worse than no section.
- **No `TBD` in a published runbook.** Move TBDs to an explicit "known gaps" section.

## Major
- **The "common 5" failure modes are covered.** Each with: how to recognize, immediate mitigation, root-cause first step, escalation criterion.
- **Commands are paste-able.** ❌ *"Restart the pods"* ✅ *`kubectl rollout restart deployment/payments-api -n payments`*
- **Dashboards / alerts linked, not inlined.** They go stale faster than the runbook.
- **Deploy and rollback are near the top**, not buried after architecture context.
- **Dependencies named** (upstream and downstream services + their on-call contacts).

## Minor
- **Order matches the 3am workflow:** active incidents → deploy/rollback → common failures → deeper context.
- **SLOs listed** with a link to where they're enforced.
- **Change calendar / freeze policy** noted if applicable.
- **Last-reviewed date** at the top.

## Nits
- Consistent command formatting (always in code blocks).
- Consistent naming for environments (`prod` not "production" in one place and "PROD" elsewhere).

## Anti-patterns to flag (always major)
- Architecture diagrams *inside* the runbook (they go stale — link to the design doc).
- Long backstory before operational commands.
- "Page X if you're not sure" without saying *what X knows that you don't*.
- Listing every Prometheus metric. Pick the 5–10 that predict outages.
- Generic "check the logs" with no log query or dashboard.

## What's working — look for
- Failure modes that name the alert that fires for them.
- Rollback that's literally one command.
- Concrete escalation criteria ("page secondary if not acknowledged in 10 min").
- Dependency table with on-call contacts for each.
- An honest "known gaps" section.

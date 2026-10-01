# Runbook — {service-name}

**Purpose:** {One sentence — what this service does}
**Owner:** {team name} (primary), {team name} (secondary)
**On-call escalation:** {PagerDuty rotation / Slack channel for paging}
**Last reviewed:** {YYYY-MM-DD}

> 📟 **Paged right now?** Skip to [Incident playbooks](#incident-playbooks) below.

## Critical links

| What | Where |
|---|---|
| Dashboard (golden signals) | {URL} |
| Logs | {URL — e.g. Datadog query, CloudWatch link} |
| Error tracking | {URL — Sentry / Bugsnag / Rollbar project} |
| Source repo | {URL} |
| Latest design doc | {URL} |
| Change calendar | {URL — to check if a recent deploy is the cause} |

## SLOs

| SLI | SLO | Window |
|---|---|---|
| Availability | 99.9% | 30 days |
| Latency p99 | < 100ms | 30 days |
| Error rate | < 0.1% | 30 days |

**Error budget:** {how much budget is left this period, link to dashboard}

## Deploy

```bash
# Trigger CI/CD
{exact command — e.g. `gh workflow run deploy-prod.yml --ref main`}

# Confirm
{exact command — e.g. `kubectl rollout status deployment/{service} -n {ns}`}
```

**Pre-deploy checklist:** {anything that must be true before deploying — error budget OK, no incidents open, …}

## Rollback

```bash
# Last-known-good
{exact command — e.g. `kubectl rollout undo deployment/{service} -n {ns}`}
```

**Rollback criteria:** {when to revert without further investigation — e.g. "error rate > 1% sustained 5 min after deploy"}

## Incident playbooks

The most common incidents, with how to recognize → mitigate → investigate.

### 1. {Incident name — e.g. "High p99 latency"}

**Symptom:** {alert text + dashboard pattern}
**Immediate mitigation:**
1. {Step — e.g. "Scale up: `kubectl scale deploy/{service} --replicas=20`"}
2. {Step}

**Investigate:**
- {Where to look — log query, dashboard, …}

**Escalate when:** {clear condition for paging the next tier}

### 2. {Incident name — e.g. "Database connection saturation"}

**Symptom:** {…}
**Immediate mitigation:** {…}
**Investigate:** {…}
**Escalate when:** {…}

### 3. {Incident name}

{…}

### 4. {Incident name}

{…}

### 5. {Incident name}

{…}

## Dependencies

| Depends on | Type | Failure mode if it's down | Owner |
|---|---|---|---|
| {Service / vendor} | {sync API / async queue / data store} | {what happens — does this service degrade, refuse traffic, or break entirely?} | {team} |
| {Service / vendor} | … | … | … |

## Operations cookbook

Common manual tasks (not incidents):

- **Drain a node / pod:** `{command}`
- **Replay a failed job:** `{command or runbook link}`
- **Re-issue an API key:** `{procedure}`
- **Triage a customer report:** `{escalation path}`

## Known gaps

- {Honest list of "we don't have a good answer for X yet" — better explicit than hidden}

## Change log

- {YYYY-MM-DD} — {what changed in the runbook itself, e.g. "added incident #5 after rollout 2026-04-12 incident"}

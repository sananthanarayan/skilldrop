---
name: delivery-metrics-report
description: Produce a delivery metrics report for one service from deployment, incident and pull-request exports — the DORA metrics (deployment frequency, change lead time, change fail rate, failed deployment recovery time) plus flow metrics (WIP, cycle time p50/p85, throughput), computed by a script with per-week trends and explicit data gaps, then interpreted for what changed and why. Use when the user wants DORA metrics, says "how are we doing on the four keys", "what's our change failure rate", "compute lead time and deploy frequency from this CSV", or "build our delivery metrics report".
---

# delivery-metrics-report

Turns raw exports (a deployments CSV, an incidents CSV and, optionally, a PR CSV) into a delivery report a team can act on. A script does all the arithmetic, so every number traces back to rows. The skill's job is to say what the trend means and what to look at next. It reports on one service over time. It is not a team scoreboard, and it refuses to become one.

It uses the metric names DORA currently publishes on [dora.dev](https://dora.dev/guides/dora-metrics/): **change lead time**, **deployment frequency**, **failed deployment recovery time** and **change fail rate**, plus **deployment rework rate** when the data supports it. Older reports called the recovery metric "time to restore service" (MTTR). This skill reports failed deployment recovery time as the DORA metric, and keeps all-incident restore time as a separately labelled context line. Definitions, column contracts and edge cases are in [`reference.md`](reference.md).

## How to respond

1. **Ask once for what is missing, then proceed.** Ask at most 2 questions. Spend them on the things that change the numbers:
   - **Which service and which window.** One service per report. Default to the last 8 full ISO weeks (Monday to Sunday) when no window is given.
   - **What counts as a failed deployment here.** The script counts `status` failed, rolled_back or hotfixed, or any deployment named in an incident's `caused_by_deploy`. If the team also counts something else, such as a feature-flag kill, add it to the export before running.

   Map the user's columns to the contract in [`reference.md`](reference.md) and rename them. Don't guess which column means "deployed". If the export comes from a deploy tool that logs every environment, keep the `environment` column. The script keeps only production rows.

2. **Say what the data can and cannot support before you run anything.** Read the headers:
   - No `first_commit_at` in either file: change lead time is not computed.
   - No incidents file and no `recovered_at`: failed deployment recovery time is not computed.
   - No `unplanned` column: rework rate is not computed.
   - No PR file: there are no flow metrics.
   Name each gap in the report. Never fill one with an estimate.

3. **Run the script.**

   ```bash
   # Claude Code
   python3 "${CLAUDE_SKILL_DIR}/scripts/delivery_metrics.py" \
     --deployments deployments.csv --incidents incidents.csv --prs prs.csv \
     --service checkout-api --from 2026-07-06 --to 2026-08-30 \
     --out out/delivery-report.md --json out/delivery-metrics.json

   # Other IDEs (from the skill folder)
   python3 scripts/delivery_metrics.py \
     --deployments deployments.csv --incidents incidents.csv --prs prs.csv \
     --service checkout-api --from 2026-07-06 --to 2026-08-30 \
     --out out/delivery-report.md --json out/delivery-metrics.json
   ```

   - Timestamps without a UTC offset stop the run (exit 2). Rerun with `--assume-tz=+00:00` only if the user confirms the zone the tool writes in. Use the `=` form so a negative offset is not read as a flag. The report counts every row that relied on the assumption.
   - Any other exit 2 names the file, line and problem. Fix the input and rerun. Don't patch around it.

4. **Check the numbers against the input before interpreting.** The deployment count should match the production rows in the window. The data-quality section lists every skipped row (missing timestamp, non-production, unresolved incident, PR with no deploy). If more than about 10% of rows were skipped, lead with that, because the metrics describe a subset.

5. **Interpret the trend, not the level.** Read the weekly series and write 3 to 6 findings. Each finding has the number, the week it moved, and the next thing to check.
   - ✅ *"Change fail rate was 0–33% in six of eight weeks and 67% (4 of 6) in the week of 2026-08-03: three rollbacks and the deploy behind INC-318. Check what changed that week before treating 12.5% as the baseline."*
   - ❌ *"Change fail rate is 12.5%, which is Elite."* That is a bucket label with no cause and no action.
   - Read p85 next to p50. A p50 of 54 min with a p85 of 23.8 h means most failures are caught by rollback, but one or two sat undetected. That points at detection (see `observability-plan`), not at the rollback process.
   - Read throughput and stability together. Deploys going up while change fail rate stays flat is the healthy pattern. Deploys going up while fail rate rises means batch size or test coverage did not keep pace.
   - With fewer than 10 observations (the script flags "low n"), give the counts and say a percentile is not yet meaningful.

6. **Refuse to rank teams or people on these numbers.** If asked to compare teams, or to set one team's numbers as another's target, say no and explain why in one paragraph:
   - DORA says the metrics apply at the application or service level, and that comparing very different applications misleads.
   - The goal is a team improving against its own past, not competing.
   - The numbers depend on local definitions: what counts as a deployment, a failure, or the start of a change. Two teams' 12% are rarely the same 12%.
   - Once a delivery metric becomes a target it gets gamed: smaller fake deploys, unlogged rollbacks, incidents not linked to deploys.
   Offer instead: each team's own trend, and a shared definition so the numbers can be read side by side for learning.

7. **Emit the report** with [`templates/delivery-report.md`](templates/delivery-report.md):
   - the scope line (service, window, week basis, metric names used)
   - the script's tables, pasted unchanged
   - findings
   - data gaps
   - what to measure next
   Hand the incident narrative to `postmortem-generator` and alerting gaps to `observability-plan`.

**Non-interactive runs** (subagent, CI, headless): a missing window defaults to the last 8 full ISO weeks, a missing service defaults to the only service in the file, and both are tagged `[assumption]` at the top. If there is no deployments file, or it holds several services and none was named, emit `BLOCKED: need a deployments CSV with deploy_id, service, deployed_at, status` or `BLOCKED: need --service (file has: <list>)`. Never type metric values the script did not produce.

## Useful references in this skill

- [`reference.md`](reference.md): the DORA definitions with their source, how each metric is computed here, the CSV column contracts, timezone and missing-field rules, and why not to compare teams
- [`templates/delivery-report.md`](templates/delivery-report.md): the report skeleton
- [`examples/checkout-api-8-weeks.md`](examples/checkout-api-8-weeks.md): the sample CSVs in this folder, the script's real output, and the interpretation written from it
- [`scripts/delivery_metrics.py`](scripts/delivery_metrics.py): the calculator (stdlib, Python 3.9+)

## Quality bar

- **Every number comes from the script's output.** Nothing is typed, rounded "for readability" into a different value, or estimated to fill a gap.
- **Metric names and definitions are stated.** The report says it uses DORA's current names and how each one is measured, including where recovery time starts.
- **One service per report.** A mixed-service file is split with `--service` or the report says it is aggregated and why that weakens it.
- **Distributions, not averages.** Lead time, recovery time and cycle time are p50 and p85 (p95 where n allows). A mean of durations is never reported.
- **Gaps are named.** Skipped rows, unresolved incidents, assumed timezones and uncomputed metrics appear in the report.
- **Findings cite a week and a count, and name a next check.** "Fail rate is high" with no week and no next step fails.
- **No team ranking or performance verdict on individuals.** Requests for one are declined with the reason.

## When to use this skill

- ✅ "Compute our DORA metrics from these deploy and incident exports."
- ✅ A quarterly or monthly delivery review for one service.
- ✅ Checking whether a change (trunk-based development, a new pipeline, smaller PRs) moved lead time or fail rate.
- ✅ Getting a WIP, cycle-time and throughput baseline from PR data.

## When NOT to use this skill

- ❌ Writing up one incident: timeline, impact, contributing factors. Use `postmortem-generator`.
- ❌ Designing SLOs, alerts or dashboards for a service. Use `observability-plan`.
- ❌ Product or business outcome metrics (activation, retention, revenue). Use `success-metrics`.
- ❌ Reporting how people use AI tools. Use `ai-usage-report`.
- ❌ Forecasting infrastructure cost or capacity. Use `capacity-cost-model`.

## Anti-patterns to avoid

- ❌ **The league table.** Ranking teams by deployment frequency or fail rate. It rewards definitional games and punishes teams with harder systems.
- ❌ **Mean time to anything.** One 52-hour failure drags a mean far from what usually happens. Use percentiles.
- ❌ **Silent timezone guessing.** Reading `2026-08-03 12:14` as UTC when the tool wrote local time shifts deploys across day and week boundaries.
- ❌ **Bucket labels as findings.** "Elite", "High" and similar cluster names come from survey data across many organisations. They are not a target for one service.
- ❌ **Counting only incidents as failures.** Rollbacks and hotfixes that never got an incident ticket are failed deployments too. Leaving them out undercounts change fail rate.
- ❌ **Trend claims from two weeks.** Under four weeks of data is a snapshot.
- ❌ **Mixing staging and production.** Counting every environment inflates deployment frequency.

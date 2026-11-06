# delivery-metrics-report: reference

## 1. Metric definitions and source

Source: DORA, "DORA's software delivery performance metrics", <https://dora.dev/guides/dora-metrics/>, checked 2026-10-01. DORA groups five metrics into throughput and instability. The quoted definitions are DORA's. The "computed here" column is this skill's choice.

| DORA metric | Group | DORA definition (quoted) | Computed here |
|---|---|---|---|
| Change lead time | Throughput | "The amount of time it takes for a change to go from committed to version control to deployed in production." | Per PR: `first_commit_at` to the `deployed_at` of its `deploy_id`. Fallback: per deployment, `deployments.first_commit_at` to `deployed_at`. Reported as p50/p85/p95. |
| Deployment frequency | Throughput | "The number of deployments over a given period or the time between deployments." | Production deployments in the window, per week, the share of days with at least one deployment, and the median gap between deployments. Failed deployments count, since they were deployments. |
| Failed deployment recovery time | Throughput | "The time it takes to recover from a deployment that fails and requires immediate intervention." | Per failed deployment: `deployed_at` to `recovered_at` if present, else to the latest `resolved_at` of the incidents that name it. Starts at the deploy, so detection lag is included on purpose: users were affected from the deploy, not from the page. |
| Change fail rate | Instability | "The ratio of deployments that require immediate intervention following a deployment." | Failed / all production deployments. Failed means `status` is failed, rolled_back or hotfixed, or an incident's `caused_by_deploy` names the deployment. |
| Deployment rework rate | Instability | "The ratio of deployments that are unplanned but happen as a result of an incident in production." | `unplanned = true` / all production deployments. Only when the column exists. |

**Naming history.** Earlier State of DevOps reports used "time to restore service", often shortened to MTTR. DORA's current page describes "the move from MTTR to Failed Deployment Recovery Time". This skill uses the current name for the DORA metric. It also reports "time to restore service (all incidents)" as a separate context line, covering every incident whether or not a deploy caused it, because on-call teams still want that number. Don't present the context line as the DORA metric.

**Lead time vs cycle time.** DORA's change lead time runs from commit to production. Flow cycle time here runs from work start (the earlier of `first_commit_at` and `opened_at`) to `merged_at`. The gap between the two is time spent waiting to deploy after merge. When lead time p50 sits well above cycle time p50, the delay is in the release process, not in review.

## 2. Flow metrics

| Metric | Computed here |
|---|---|
| WIP | PRs started before each week-end snapshot (Monday 00:00 UTC, or the day after the window ends) and not yet merged or closed at that moment. |
| Cycle time | Start (above) to `merged_at`, for PRs merged in the window. p50 and p85. p85 is the planning number: "85% of changes merge within X". |
| Throughput | PRs merged per ISO week. Closed-unmerged PRs are counted as abandoned and kept out of throughput. |

Little's Law (average WIP = throughput × average cycle time) holds only for a stable system. Use it as a sanity check on the series, not as a forecast.

## 3. Input column contracts

Header names are matched exactly (case-sensitive). Rename columns in the export before running. Extra columns are ignored.

**deployments.csv** (required)

| Column | Required | Notes |
|---|---|---|
| `deploy_id` | yes | Unique per deployment. Incidents and PRs refer to it. |
| `service` | yes | Filtered with `--service`. |
| `deployed_at` | yes | ISO 8601 with offset. Empty rows are skipped and counted. |
| `status` | yes | `success`/`succeeded`/`ok`, or `failed`/`rolled_back`/`rollback`/`hotfixed`. Anything else is an error. |
| `environment` | no | If present, only `production`/`prod` rows are kept. Empty is treated as production. |
| `first_commit_at` | no | Earliest commit in the deployment. Enables lead time without a PR file. |
| `recovered_at` | no | When service was restored after a failed deploy (for example, rollback complete). |
| `unplanned` | no | true/false. Enables rework rate. |

**incidents.csv** (optional)

| Column | Required | Notes |
|---|---|---|
| `incident_id`, `service`, `started_at` | yes | `started_at` is impact start, not ticket creation, where the tool records both. |
| `resolved_at` | yes (column) | Empty means unresolved: excluded from restore times and counted. |
| `caused_by_deploy` | no | A `deploy_id`. Marks that deployment failed and supplies its recovery end. |
| `severity` | no | Carried through, not used in the arithmetic. |

**prs.csv** (optional)

| Column | Required | Notes |
|---|---|---|
| `pr_id`, `opened_at`, `merged_at` | yes | Empty `merged_at` means not merged. |
| `first_commit_at` | no | Needed for lead time, and makes cycle time start at the first commit. |
| `deploy_id` | no | Needed for lead time. |
| `closed_at` | no | Closed-unmerged PRs count as abandoned and end WIP. |
| `service` | no | Filtered with `--service` when present. Otherwise filter the export to one service first. |

Typical sources: deploy events from the CD tool (Argo CD, GitHub Actions deployments API, Spinnaker), incidents from the incident tool (PagerDuty, incident.io, Jira Service Management), and PRs from the Git host's API. Each tool names fields differently, so map them to the columns above.

## 4. Timezones, windows and missing fields

- Every timestamp must carry an offset (`Z`, `+01:00`). The script converts everything to UTC.
- A timestamp with no offset is an error. `--assume-tz=<offset>` applies one offset to all such values, and the report counts them. Pass a fixed offset, not a zone name. If the source wrote local time across a daylight-saving change, a fixed offset is wrong for part of the window. Fix the export instead.
- Weeks are ISO weeks (Monday start) in UTC. A window that doesn't start on a Monday or end on a Sunday makes the edge weeks partial, and the report says so.
- `--from` and `--to` are inclusive UTC dates. Incidents are kept by `started_at` and PRs by `merged_at` within the window.
- Fewer than 10 observations in a distribution is flagged "low n".
- Percentiles use linear interpolation between closest ranks, the same method as numpy's default.

## 5. Why these numbers must not rank teams

- **DORA says so.** The metrics "are meant to be applied at the application or service level. Comparing metrics between vastly different applications (for example, a mobile app and a mainframe system) can be misleading." And: "The goal is to improve your team's performance over time, not to compete against other teams or organizations." (dora.dev, as above.)
- **The definitions are local.** What counts as a deployment (each canary step? each microservice?), a failure (rollback only? flag kill?) and the start of a change differ between teams. The same label hides different measurements.
- **The context differs.** A regulated batch system and a stateless web front end face different constraints. A gap between them describes the systems, not the teams.
- **Targets get gamed.** Ranked on deploys, teams split deploys. Ranked on fail rate, they stop linking incidents to deploys. Both make the numbers worse as information.

When asked for a comparison, offer: each team's own trend over the same window, and an agreed definition of deployment and failure, so teams can learn from each other's practices without a leaderboard.

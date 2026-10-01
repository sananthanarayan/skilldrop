# Dashboard spec: <dashboard name>

**Audience:** <role(s)> · **Owner:** <role, team> · **Tool:** <BI tool, or "not chosen">
**Decision:** <who> decides <what> <how often>, using this dashboard.

## Questions, in priority order

| # | Question | If the answer is bad, they… |
|---|---|---|
| 1 | <question the audience asks out loud> | <action> |
| 2 | <...> | <...> |

## Charts

| # | Chart | Type | Why this type | Metric (defined name) | Grain · window · comparison |
|---|---|---|---|---|---|
| 1 | <title stating the question> | <line / sorted bar / number tile / table …> | <one line> | `<metric_name>` or `undefined: needs a spec before build` | <daily · last 8 weeks · vs target> |

## Filters

| Filter | Default | Applies to | Notes |
|---|---|---|---|
| <date range> | <last complete week> | <all> | |

Left off as filters: <dimension> — <why, e.g. fans out order-level metrics>

## Refresh and freshness

- **Refresh:** <cadence>
- **Freshness SLA:** <data no older than … by …>
- **When stale:** <visible banner naming the owner>
- **"Data as of" timestamp:** shown <where>

## Layout

```
+-----------------------------+-----------------------------+
| Q1: <chart>                                               |
+-----------------------------+-----------------------------+
| Q2: <chart>                 | Q3: <chart>                 |
+-----------------------------+-----------------------------+
| Detail table                                              |
+-----------------------------------------------------------+
```

## Deliberately left off

| Requested item | Why it's cut |
|---|---|
| <metric or chart> | <fails the vanity test / audience can't act on it / duplicates Q2 / belongs on another dashboard> |

## Open questions

- [ ] <undefined metric> — needs a `metric-definition` spec, owner <role>
- [ ] <data gap or unconfirmed target>

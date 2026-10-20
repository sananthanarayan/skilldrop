# Payments API runbook

Service `payments-api` runs three replicas in the `payments` namespace. On-call rota:
**payments-primary**. Escalation: the payments lead on the rota.

> **Warning:** Never restart all three replicas at once. Restart one, wait for it to pass
> its health checks, then move to the next.

## Health checks

| Check | Where | Healthy |
|---|---|:---:|
| Liveness | `GET /healthz` on each replica | `200` |
| Queue depth | `qctl depth payments-out` | under 500 |
| p95 latency | Grafana, "Payments overview" | under 300 ms |

![p95 latency panel on the Payments overview dashboard](img/latency-dashboard.png)

## Restart one replica

1. Mark the replica out of rotation:

```bash
kubectl -n payments label pod payments-api-0 rotation=out --overwrite
```

2. Delete the pod and let the deployment recreate it:

```bash
kubectl -n payments delete pod payments-api-0
```

3. Wait until `/healthz` returns `200` and queue depth is under 500 before the next replica.

> **Note:** The latency alert below fires at 0.3 s. A restart alone rarely clears it if the
> card-network gateway is slow; check the gateway status page first.

## Latency alert definition

The alert lives in `alerts/payments.xml`:

```xml
<alert name="payments-p95-latency" severity="page">
  <query><![CDATA[histogram_quantile(0.95, rate(payments_http_seconds_bucket[5m])) > 0.3]]></query>
  <for>10m</for>
</alert>
```

<details><summary>Rollback, if the restart did not help</summary>
<ol>
<li>Run <code>helm -n payments rollback payments-api</code> to return to the previous release.</li>
<li>Page the payments lead if the error rate is still above 2% ten minutes after the rollback.</li>
</ol>
</details>

## After the incident

- [ ] Note the start and end time in the incident channel
- [ ] Link the Grafana panel for the window
- [x] Confirm the alert has cleared

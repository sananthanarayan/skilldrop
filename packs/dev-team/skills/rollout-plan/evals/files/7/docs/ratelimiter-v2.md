# Rate limiter v2 (api-gateway)

## Why
v1 is an in-memory token bucket per gateway pod. With 18 pods behind the LB a tenant's
effective limit is roughly 18x the configured one and moves with autoscaling. Enterprise
contracts signed for Q4 specify hard per-tenant limits, so we need a global limit.

## Design
- Sliding-window counter per (tenant_id, route_group) in the shared Redis cluster
  (`redis-gw`, also used for session cache).
- One INCR + EXPIRE pipeline per request, ~1 ms budget.
- On Redis error or timeout (> 5 ms): fail open, allow the request, emit `rl_v2.redis_error`.
- Returns 429 with `Retry-After`.
- Flag: `gateway.ratelimit_v2` in our flag service. Supports percentage rollout,
  bucketing key configurable (default: request_id), and per-tenant allow/deny lists.

## Metrics already emitted
- `gw.requests` / `gw.responses{status}` per tenant
- `gw.latency_ms` p50/p95/p99
- `rl_v1.throttled` per tenant
- `rl_v2.*` - not yet wired to dashboards

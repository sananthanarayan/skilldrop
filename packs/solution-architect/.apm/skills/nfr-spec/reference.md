# nfr-spec reference — category catalog, archetype defaults, verification menu

Defaults are starting points, always tagged `[assumption]` in the output. The archetype row is chosen once in step 1 and reused everywhere.

## Archetypes

| Archetype | Examples | Posture |
|---|---|---|
| customer-facing SaaS | checkout, dashboards | user-perceived latency and availability dominate |
| internal tool | admin panels, back-office | availability honesty — business hours usually suffice |
| public API | partner integrations | contract stability, rate limits, versioning weight |
| batch / pipeline | ETL, reports, billing runs | completion deadlines and replayability, not latency |
| mobile / edge | apps, POS | offline behavior, payload size, OS-version spread |

## Category catalog (sweep all 11 — every one lands in target / n/a+reason / default+tag)

### 1. Performance / latency
Target shape: `p50/p95 < N ms for {operation} at {load}`. Per key operation, not uniform.
Defaults: SaaS interactive p95 < 500ms; internal tool p95 < 2s; API p95 < 300ms; batch n/a → see deadline; mobile interaction < 100ms perceived.

### 2. Throughput / capacity
Target shape: `sustains N rps / M jobs/hr at target latency; designed headroom ×K`.
Defaults: 2× current peak headroom; batch: completes within window at 3× current data volume.

### 3. Availability / SLO
Target shape: `N% monthly, measured at {user-visible boundary}; error budget stated`.
Defaults: SaaS 99.9%; internal tool 99.5% business-hours; public API 99.95%; batch: deadline-based ("billing run completes by 06:00, 99% of months").
Calibrate with the down-for-an-hour answer; name the cost when exceeding the default — each nine roughly 10×es the engineering.

### 4. Durability / backup / DR
Target shape: `RPO ≤ N min, RTO ≤ M min; backup restore rehearsed {cadence}`.
Defaults: transactional data RPO ≤ 5 min / RTO ≤ 1h; derived/rebuildable data RPO n/a with reason "recomputable from source in N h".

### 5. Privacy / retention / residency
Per data class: what's stored · classification (PII? payment? health?) · retention period · deletion mechanism (user-triggered / TTL / legal hold) · residency constraint.
Default: no new PII without a named retention period; "indefinite" written explicitly as a decision.

### 6. Accessibility
Target shape: `WCAG {version} {level} on {scope}; verified by {automated + manual}`.
Defaults: customer-facing WCAG 2.2 AA; internal tools AA for core flows `[assumption — confirm with HR/legal jurisdiction]`.

### 7. Internationalization / localization
Target shape: locales supported at launch; text expansion tolerance; date/number/currency handling; RTL yes/no.
Default: single-locale launch is fine **if stated**; unicode-correct storage is non-negotiable either way.

### 8. Observability
Requirement shape: the 3am questions — `on-call can answer {question} within {time}` — plus alert conditions with thresholds and a paging severity. Tool names excluded.
Default minimum: error rate, latency, and saturation per surface; alert before users notice (burn-rate, not static threshold, for SLO'd surfaces); every alert maps to a runbook entry (→ `runbook-generator`).

### 9. Operability
Deploy/rollback time targets, config-change blast radius, feature-flag kill switch, dependency-down behavior (degrade vs fail closed — chosen per dependency).
Default: rollback ≤ 15 min; every new external dependency gets an explicit down-behavior.

### 10. Compatibility
Browsers/devices/OS floor; API consumer versions honored; data-format backward compatibility window.
Default: SaaS = last 2 major browser versions; API = no breaking change without version bump (→ `api-contract-draft` policy).

### 11. Cost
Target shape: `≤ $N/month at target volume; alert at 80%`. Include the per-unit driver (per-tenant, per-GB, per-1k-requests).
Default: projection required before launch; "we'll see" fails the ledger.

## Verification menu (every target picks at least one)

| Method | Proves |
|---|---|
| Load test at stated volume + headroom | latency, throughput |
| Chaos / dependency-kill drill | availability, dependency-down behavior |
| Backup-restore rehearsal (timed) | RPO/RTO are real, not configured |
| Deletion end-to-end test (incl. backups/replicas) | retention/deletion actually deletes |
| axe-core + manual screen-reader pass | accessibility level on scope |
| Pseudo-locale build (text expansion, RTL) | i18n readiness |
| Game-day: answer the 3am questions on a stage incident | observability requirements |
| Timed rollback drill | operability targets |
| Cost projection reviewed against first month's bill | cost model honesty |

# Agent budget: {workflow name}

> Outcome unit: {one successful …} · Status: {design-time [assumption] | calibrated on {N} runs} · Owner: {role}

## Stage budgets

| Stage | Tier | Why this tier | Expected / run | Cap (hard) | On cap |
|---|---|---|---|---|---|
| {stage} | light / standard / heavy | {one line} | {tokens ≈ ${…} `[assumption]`?} | {3–5× expected, tokens ≈ $; per-item + stage-wide for fan-out stages} | abort→escalate / degrade rung {n} / per-item: fail item to needs-human, continue rest |

**Run-level cap:** ${number, < sum of stage caps in currency — the only unit that sums across tiers} — all stages capping at once is an anomaly to stop, not a run to finish.

## Degradation ladder (in order; trigger and owner per rung)

1. Narrow scope — {fewer items per run} · trigger: {…} · flipped by: {role}
2. Reduce parallelism — {smaller fleet} · trigger: {…}
3. Cut non-verification stages — {which} · trigger: {…}
4. **Verification is never cut.** A workflow that can't afford its verifier can't afford to run.

## Cost per outcome

- **Target:** {spend ÷ successful outcomes} · review threshold: {value that triggers investigation}
- **Comparison line:** the same outcome today costs {manual process, time × rate} — the number that says whether this is cheap.

## Measurement

- Spend logged per run, per stage (stage-tagged; feeds the loop spec's telemetry row)
- {cadence} review of cost-per-outcome + cap-hit counts by {role}
- Alerts: cap-hit rate rising ({threshold}) → drift investigation · run-level cap breached → incident, not a line item
- Calibration: replace `[assumption]` expecteds after {~20} real runs · date: {…}

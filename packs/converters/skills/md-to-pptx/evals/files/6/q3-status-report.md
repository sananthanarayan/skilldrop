# Harbourline Ledger Migration — Q3 Status

Prepared for the Pellworth Insurance steering committee, 24 October 2026.

## Summary

- Overall status: **Amber**
- 3 of 4 Q3 milestones met
- Cutover rehearsal moved from 6 Nov to 13 Nov
- No change to the go-live date of 4 Dec

## Milestones

| Milestone | Owner | Due | Status |
|---|---|---|---|
| Chart of accounts mapped | Dana Okafor | 15 Aug | Done |
| Historic ledger load (2019–2025) | Mirek Sato | 12 Sep | Done |
| Reconciliation sign-off | Priya Lindqvist | 30 Sep | Done |
| Cutover rehearsal 1 | Mirek Sato | 6 Nov | Moved to 13 Nov |

## Risks

- Reconciliation variance on intercompany accounts
  - 212 open items, down from 640 in August
  - Target: under 50 before rehearsal
- Key-person dependency on the legacy batch scheduler
  - Only one Pellworth engineer knows the job chain
  - Knowledge-transfer sessions booked for w/c 2 Nov
- Downstream reporting team not yet trained

## Burn-up

![Story-point burn-up, Sprints 1–9](img/burnup.png)

Scope grew by 40 points in Sprint 7 after the intercompany change request.

## Budget

- Spend to date: £1.18m of £1.65m approved
- Forecast at completion: £1.62m
- Change request CR-07 (intercompany rules) awaiting Pellworth sign-off

<!-- internal only: contractor spend is actually 14% over plan; the forecast above assumes CR-07 is approved. Do not raise with Pellworth until CR-07 is signed. -->

## Workstream updates

- Data: 2019 ledger reloaded after currency-code fix
- Data: 2020–2022 ledgers reconciled to the penny
- Data: 2023 ledger has 38 open variances
- Data: 2024–2025 ledgers loaded, reconciliation starts w/c 2 Nov
- Data: archive extract for pre-2019 agreed as read-only
- Integration: payroll feed tested end to end
- Integration: claims feed tested, one mapping defect open (DEF-311)
- Integration: bank statement import passing in test
- Integration: FX rates feed switched to the new provider endpoint
- Integration: legacy batch scheduler jobs inventoried (147 jobs)
- Reporting: 22 of 31 management reports rebuilt
- Reporting: board pack template agreed with Finance
- Reporting: regulatory return QRT-S.02 still on the legacy system
- Reporting: report owners named for all 31 reports
- Testing: system test cycle 2 complete, 94% pass rate
- Testing: performance test scheduled for 9 Nov
- Testing: user acceptance testing plan signed off
- Change: training materials drafted for Accounts Payable
- Change: super-user network has 14 named people
- Change: comms plan for go-live week drafted

## Next steps

1. Pellworth to sign CR-07 by 31 Oct
2. Cutover rehearsal 1 on 13 Nov
3. Steering committee decision on go-live, 27 Nov

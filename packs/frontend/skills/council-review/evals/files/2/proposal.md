# Proposal: move the telemetry historian to a hosted service

Glenmarra Water - Operations Technology
Author: Iain Corbett, OT Lead
Status: for steering group decision

## Summary

We propose retiring the on-site telemetry historian at Balnagown Treatment Works and moving all telemetry data to StreamVault, a hosted historian service. We also propose replacing the remote telemetry units (RTUs) at our 46 pumping stations with cheaper cellular sensor gateways that send readings straight to StreamVault.

## Current setup

- 46 pumping stations and 3 service reservoirs report flow, level, pump status and chlorine residual.
- Each station's RTU stores readings locally (up to 72 hours) and forwards them to the on-site historian over cellular or licensed radio.
- The on-site historian runs on two servers at Balnagown, supported by Kellbrook Systems.

## Proposed setup

- Sensor gateways at each station post readings directly to StreamVault over cellular.
- Because StreamVault offers 99.99% availability, local buffering at the stations is no longer needed, so the gateways we have chosen have no local storage. This is what makes them cheaper than RTUs.
- The Balnagown servers are decommissioned.

## Cost

| | Annual cost |
|---|---|
| Current (servers, Kellbrook support, RTU maintenance, radio licences) | £310k |
| Proposed (StreamVault subscription, gateway maintenance, cellular data) | £215k |
| **Annual saving** | **£120k** |

One-off cost of gateways and migration: £540k.

## Why now

Kellbrook ends support for our historian in 2027, so we have to decide this quarter or run unsupported software.

## Rollout

Migrate all 46 stations over a single weekend in February 2027, then decommission the servers the following week.

# TideFeed: service notes

Owner: Port Systems team, Saltholm Harbour Authority

## What it does

TideFeed collects water-level readings from the four tide gauges in the harbour (North Pier, Inner Basin, Lock Gate, Outer Mark) every minute and publishes the current level and the next 6 hours of predicted levels to the pilots' berthing display and to harbour control.

## Components

- **gauge-collector**: polls the four gauges over the harbour radio link. Runs on the VM `tidefeed-app-01`.
- **tidefeed-api**: serves levels to the berthing display. Same VM.
- **PostgreSQL** on `tidefeed-db-01`: stores readings.
- Both VMs sit in the harbour authority's own server room.

## Deploying

Deploys use `deploy.sh` from the ops laptop. To roll back, run `./deploy.sh --rollback`.

Database migrations run automatically on deploy. Migration 0042 (October 2026) split the readings table by gauge and is forward-only: there is no down migration, and app versions before 2.6.0 do not work against the new schema.

## Contacts

- Harbour IT service desk: ext. 4410, staffed 08:00 to 18:00.
- Out of hours: the Port Systems on-call engineer, via the harbour control room.
- Gauge hardware: Meridian Gauges support line (contract ref MG-2291).

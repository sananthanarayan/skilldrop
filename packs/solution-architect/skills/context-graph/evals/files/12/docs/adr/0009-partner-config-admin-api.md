# ADR-0009: Partner configuration via an admin API

- Status: Accepted
- Date: 2024-05-13
- Governs: `src/partners/`, `migrations/004_partners.sql`

## Context
We now have 60+ partners and onboarding through a YAML PR and a deploy takes days.

## Decision
Partner configuration is stored in the `partners` table and edited through an internal admin API.
The service reloads partners from the table every 60 seconds. See ADR-0011 for the authentication
model of the admin API.

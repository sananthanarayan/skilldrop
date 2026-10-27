# ADR-0008: Partner configuration in a YAML file

- Status: Accepted
- Date: 2023-11-20
- Governs: `config/partners.yaml`, `src/partners/`

## Decision
Partner endpoints, enabled event types and secret references live in `config/partners.yaml`,
reviewed by pull request. The service loads the file at startup.

## Consequences
Onboarding a partner needs a deploy. Acceptable at our current 12 partners.

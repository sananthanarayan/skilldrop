# ADR-0001: Monorepo layout

- Status: Accepted
- Date: 2023-02-10
- Deciders: Platform team (H. Okafor, L. Brandt)
- Governs: `services/`, `libs/`

## Decision
One repository. Each deployable service gets its own folder under `services/<name>/`; shared code goes
under `libs/`. A service folder is never shared by two deployables.

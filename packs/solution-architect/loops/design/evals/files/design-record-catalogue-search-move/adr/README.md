# Kettleby Home ADRs: how we write them

- File name `ADR-NNNN-short-title.md`; the next ADR takes the next number after the
  highest in the index.
- **Sections, in this order:** Status, Context, Decision, Consequences and risks,
  Alternatives considered.
- **Status** is `Proposed`, `Accepted` or `Superseded by ADR-NNNN`. A decision that has
  already been made and is being recorded after the fact is written as `Accepted`, with a
  `Decided by:` line naming the person and the date.
- **Consequences and risks** lists every known risk, with an owner or a mitigation for
  each. Do not leave a risk without one or the other.
- **Partial replacement.** When a new ADR replaces only part of an older one, do *not*
  mark the older ADR `Superseded`. Add `Amended by ADR-NNNN` under its status, and say
  in the new ADR exactly which parts of the old one still stand. `Superseded` is only for
  a full replacement.
- Keep it to one page.

## Index

| ADR | Title | Status |
| --- | --- | --- |
| ADR-0009 | Catalogue database on managed Postgres | Accepted |
| ADR-0010 | Single primary, no read replicas | Accepted |
| ADR-0011 | Self-hosted search cluster for catalogue and help-centre search | Accepted |
| ADR-0012 | Checkout latency budget | Accepted |

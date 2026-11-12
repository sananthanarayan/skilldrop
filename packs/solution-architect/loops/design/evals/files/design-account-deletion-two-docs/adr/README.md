# Architecture decision records: house rules

1. **One decision per ADR.** File name `ADR-NNNN-short-title.md`.
2. **Numbering.** The next ADR takes the next unused number. Numbers are never reused,
   including for withdrawn ADRs (see the index).
3. **Status.** One of `Proposed`, `Accepted`, `Superseded by ADR-NNNN`. A new ADR is
   always written as `Proposed`. Only the architecture review group marks an ADR
   `Accepted`; the author never does.
4. **Sections, in this order:** Context, Decision, Consequences, Alternatives considered.
5. **Relates to.** Directly under the title, list every existing ADR the decision relies
   on or constrains itself by.
6. **Length.** An ADR fits on one page. Detail belongs in a design doc linked from it.

## Index

| ADR | Title | Status |
| --- | --- | --- |
| ADR-0001 | Record architecture decisions | Accepted |
| ADR-0002 | Postgres is the system of record | Accepted |
| ADR-0004 | Background work runs on the Postgres job queue | Accepted |
| ADR-0005 | Media store for member photos | Accepted |
| ADR-0006 | Nightly backups are immutable for 35 days | Accepted |
| ADR-0007 | Pseudonymised nightly copy to the analytics warehouse | Accepted |
| ADR-0008 | Event streaming via a hosted broker | Withdrawn (number retired) |

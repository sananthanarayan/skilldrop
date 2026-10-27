# ADR-0001: Record architecture decisions

- Status: Accepted
- Date: 2023-01-09
- Deciders: Priya Okafor, Tomasz Lind

## Context

Ledgerline is growing past the two people who wrote it. Decisions live in Slack threads.

## Decision

We will record significant architecture decisions as numbered Markdown files in `docs/adr/`.
A decision that replaces an earlier one says so in a `Supersedes:` line, and the earlier
record's status is changed to `Superseded by ADR-NNNN`.

## Consequences

Every new ADR is reviewed in the same PR as the code it governs.

# ADR-007: Move billing-service persistence from Hibernate to jOOQ

Status: Accepted (2026-09-14)

## Context

Hibernate has bitten us three times this year: lazy-loading surprises in the
PDF renderer, a dirty-checking flush that wrote a half-updated invoice during an
exception, and slow startup from entity scanning. Most of our queries are
already hand-written JPQL or native SQL.

## Decision

Replace Hibernate/Spring Data JPA with jOOQ in billing-service during Q1 2027.

## Precondition

The ORM swap must be a persistence-only change. Before it starts, invoice
business rules (totals, tax, late fees, payment state transitions) must live in
code that does not import `jakarta.persistence` or depend on `EntityManager`,
and must be testable without a database.

## Out of scope

- Changing tax or late-fee rules.
- The reporting database (separate service).

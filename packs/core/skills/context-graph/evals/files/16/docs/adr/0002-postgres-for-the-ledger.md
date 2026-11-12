# ADR-0002: Postgres for the payment ledger

Status: Accepted
Date: 2025-01-20
Deciders: Priya Natarajan, Tomás Okafor
Governs: services/payments/ledger.py

## Decision

The ledger of record is a single Postgres database. Every payment is written in
one transaction to `payments` and `ledger_entries`.

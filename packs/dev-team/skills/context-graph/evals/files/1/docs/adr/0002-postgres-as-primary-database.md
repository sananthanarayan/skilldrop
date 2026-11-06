---
status: accepted
date: 2024-03-12
deciders: platform team
---

# Use Postgres as the primary database

## Context and Problem Statement

The API needs one relational store for accounts, orders and audit history.

## Decision Outcome

Chosen option: "Postgres", because the team already runs it and it gives us transactions across
accounts and orders. Access goes through `services/api/db.py`.

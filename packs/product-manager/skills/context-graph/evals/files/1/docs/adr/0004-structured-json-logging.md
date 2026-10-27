---
status: accepted
date: 2024-07-02
---

# Structured JSON logging

## Context and Problem Statement

Log lines are free text and hard to search.

## Decision Outcome

Every service logs one JSON object per line with `request_id`, `level` and `msg`. The shared
helper is `services/api/logging_setup.py`.

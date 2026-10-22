---
id: RFC-0003
title: Retry policy for the ingest service
status: accepted
date: 2025-03-11
authors: [Oskar Byrne]
governs: [services/ingest/retry.ts]
cites: [RFC-0001]
---

# RFC-0003: Retry policy for the ingest service

## Context

INC-114 (2025-02-27): the partner feed API returned 503 for four minutes. Every ingest worker
retried on a fixed 1 s interval, the retries stayed synchronised, and the partner rate-limited
our whole account for two hours after recovery.

## Decision

Ingest retries use exponential backoff with full jitter: base 200 ms, cap 30 s, at most
6 attempts. Fixed-interval retries are not allowed in ingest.

## Consequences

Worst-case retry window is about 60 s per request. Dashboards alert on attempt 5+.

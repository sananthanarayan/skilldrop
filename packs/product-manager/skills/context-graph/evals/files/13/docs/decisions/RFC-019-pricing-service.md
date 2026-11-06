# RFC-019: Read prices from pricing-svc instead of the ERP

Status: Proposed
Date: 2025-03-18
Author: P. Achterberg
Supersedes: RFC-008

## Context
The pricing team now runs `pricing-svc`, a REST service that replicates ERP prices within
5 seconds of a change. It has no per-client rate limit and a p95 of 35 ms.

## Proposal
Shopfront calls `GET {PRICING_SVC_URL}/v1/prices/{sku}` instead of the ERP SOAP call, and
`erp_client.py` is deleted.

## Open questions
- Do we still need the Redis cache from RFC-012 once the ERP is out of the path?

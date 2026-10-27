---
id: RFC-0007
title: Send webhooks from the job queue
status: proposed
date: 2025-09-15
---

## Proposal

Move delivery out of `services/payments/webhooks/` and onto the shared job queue, so retries
survive a deploy. Open questions: who owns the queue, and whether payment events may leave the
payments boundary in RFC-0002.

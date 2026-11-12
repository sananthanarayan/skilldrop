---
id: DR-016
title: Move order attributes into a separate order_attributes table
status: Proposed
date: 2026-09-30
cites: [DR-014]
---

Proposal (under discussion, not agreed): replace the `orders.attributes` JSON column from
DR-014 with an `order_attributes(order_id, key, value)` table so attributes can be indexed.
Open question: whether existing keys are back-filled or dual-written.

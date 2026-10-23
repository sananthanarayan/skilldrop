---
id: RFC-0002
title: Payments service boundary
status: accepted
date: 2024-06-10
authors: payments team
---

## Decision

Everything under `services/payments/` is owned by the payments team. Changes there need a review
from a payments engineer, and no other service imports from it directly; they call its API.

## Why

"Card data and payment state stay behind one boundary, so the audit scope stays one service wide."

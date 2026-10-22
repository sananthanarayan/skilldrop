---
id: DR-009
title: Order line items are immutable once the order is placed
status: Accepted
date: 2023-01-30
governs: [app/models/line_item.py]
cites: [DR-003]
---

After an order moves to `placed`, its line items are never updated. Price or quantity
corrections are written as rows in `order_adjustments`, amounts in minor units per DR-003.

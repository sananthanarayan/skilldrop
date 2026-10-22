---
id: DR-003
title: Store money as integer minor units with a currency code
status: Accepted
date: 2022-02-17
governs: [app/models/order.py, app/models/line_item.py]
---

All monetary amounts are stored as integer minor units (`*_minor`, e.g. pence) alongside a
three-letter `currency` column. No floats or decimals for money anywhere in the schema.

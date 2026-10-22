---
id: DR-014
title: Optional customer-supplied order fields go in orders.attributes
status: Accepted
date: 2024-02-08
amends: DR-005
governs: [app/models/order.py, migrations/0012_add_order_attributes.sql]
---

DR-005's typed-columns rule produced a migration for every small checkout tweak. We relax it:

- New **optional, customer-supplied** fields that are not filtered, joined or reported on
  (delivery notes, gift options, and similar) are stored as keys in the `orders.attributes`
  JSON column. Each key is listed in `ORDER_ATTRIBUTE_KEYS` in `app/models/order.py` and is
  reviewed like a column.
- Anything we filter, join, index or report on stays a typed column, as DR-005 says.

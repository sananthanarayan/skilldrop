---
id: DR-005
title: Orders table uses typed columns only
status: Accepted
date: 2022-04-11
governs: [app/models/order.py, migrations/]
---

Every field on an order is a typed, named column with a migration. We do not store JSON blobs
on the orders table: they hide schema changes from review and cannot be indexed.

# Warehouse schema notes (PostgreSQL 15, schema `subs`)

All timestamps are `timestamptz` stored in UTC. The business runs on Europe/London time.

## subs.subscribers
One row per subscriber account.
| column | type | notes |
|---|---|---|
| subscriber_id | bigint PK | |
| email | text | |
| plan | text | Classic, Veggie, Family, Lean. Current plan only |
| created_at | timestamptz | sign-up time |
| cancelled_at | timestamptz | NULL while active; set when the subscription is cancelled |

## subs.orders
One row per weekly box delivered.
| column | type | notes |
|---|---|---|
| order_id | bigint PK | |
| subscriber_id | bigint FK | |
| plan | text | plan at time of order |
| order_total_pence | integer | total charged for the box, incl. add-ons |
| ordered_at | timestamptz | |

## subs.order_items
One row per line item in a box (recipes and add-ons). A box usually has 3 to 6 items.
| column | type | notes |
|---|---|---|
| order_item_id | bigint PK | |
| order_id | bigint FK | |
| sku | text | |
| item_price_pence | integer | |

## subs.refunds
Zero or more rows per order (partial refunds are common, e.g. one missing ingredient).
| column | type | notes |
|---|---|---|
| refund_id | bigint PK | |
| order_id | bigint FK | |
| refund_pence | integer | |
| refunded_at | timestamptz | |

## subs.test_accounts
Accounts used by QA and the warehouse team. Some rows are placeholder accounts created
before the subscriber was provisioned, so `subscriber_id` can be NULL.
| column | type | notes |
|---|---|---|
| email | text | |
| subscriber_id | bigint | nullable |

## subs.winback_offers
| column | type | notes |
|---|---|---|
| offer_id | bigint PK | |
| subscriber_id | bigint FK | |
| sent_at | timestamptz | |
| offer_code | text | |
| redeemed_at | timestamptz | NULL if not redeemed |

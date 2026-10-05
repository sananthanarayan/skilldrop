# Tallow & Thyme: tables (Postgres 15)

All timestamps are `timestamptz`, stored in UTC. The business reports on UK time.

## orders

| Column | Type | Notes |
|---|---|---|
| order_id | bigint | primary key |
| customer_id | bigint | references customers |
| store | text | 'uk' or 'eu' |
| currency | text | 'GBP' for the uk store, 'EUR' for the eu store |
| gross_amount_minor | integer | order total in pence (GBP) or cents (EUR) |
| placed_at | timestamptz | when the order was placed |
| status | text | 'placed', 'delivered', 'cancelled' |
| is_test | boolean | true for orders made by the test harness |

## refunds

| Column | Type | Notes |
|---|---|---|
| refund_id | bigint | primary key |
| order_id | bigint | references orders |
| amount_minor | integer | in the same currency as the order |
| reason | text | free text typed by the CX agent |
| created_at | timestamptz | when the refund was issued |

An order can have more than one refund row: a missing ingredient is refunded, then a second
problem with the same box is refunded later. About 1 in 9 refunded orders has two or more
rows.

## customers

| Column | Type | Notes |
|---|---|---|
| customer_id | bigint | primary key |
| email | text | |
| created_at | timestamptz | |

## Not in the database

There is no exchange-rate table. Finance converts EUR to GBP by hand in a spreadsheet.

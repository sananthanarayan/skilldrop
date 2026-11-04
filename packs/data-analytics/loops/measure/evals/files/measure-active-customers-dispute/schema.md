# Schema notes: Ovenbird (bakery scheduling software), PostgreSQL 15, schema `app`

A **customer** is a business account (one bakery or bakery chain). A customer has one or
more **users** (staff seats). Billing is per customer, monthly or annual.

All timestamps are `timestamptz`, stored in UTC.

## app.customers
| column | type | notes |
|---|---|---|
| customer_id | bigint PK | |
| name | text | |
| status | text | `trial`, `active`, `cancelled` |
| billing_interval | text | `monthly` or `annual` |
| created_at | timestamptz | |
| cancelled_at | timestamptz | NULL unless cancelled |

## app.users
One row per staff seat. A customer has between 1 and 60 users; the median is 3.
| column | type | notes |
|---|---|---|
| user_id | bigint PK | |
| customer_id | bigint FK | |
| email | text | |
| last_login_at | timestamptz | overwritten on every login; only the most recent login is kept |

## app.login_events
One row per login. Retained for 13 months.
| column | type | notes |
|---|---|---|
| login_id | bigint PK | |
| user_id | bigint FK | |
| logged_in_at | timestamptz | |

## app.payments
One row per payment attempt.
| column | type | notes |
|---|---|---|
| payment_id | bigint PK | |
| customer_id | bigint FK | |
| amount_pence | integer | |
| status | text | `succeeded`, `failed`, `refunded` |
| paid_at | timestamptz | |

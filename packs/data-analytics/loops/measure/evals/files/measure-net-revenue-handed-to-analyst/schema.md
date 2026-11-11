# Schema (PostgreSQL 16)

All timestamps are stored in UTC. The business reports in calendar months in Europe/London.

- `orders(order_id, channel, ordered_at timestamptz, status, order_total numeric)` - `order_total`
  includes VAT and shipping. `status` is never NULL; values: placed, dispatched, cancelled.
- `order_lines(line_id, order_id, sku, qty, line_net numeric, dispatched_at timestamptz NULL)` -
  `line_net` excludes VAT and shipping. Orders have 3 lines on average.
- `refunds(refund_id, order_id, refunded_at timestamptz, amount_net numeric, reason text NULL)` -
  `amount_net` excludes VAT. `reason` is NULL for refunds customers raise themselves on the
  website, which is most refunds. `reason = 'test'` marks refunds raised by the QA team.

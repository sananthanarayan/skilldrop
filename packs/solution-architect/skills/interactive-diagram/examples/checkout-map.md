# Worked example — what a checkout request touches

## Input

> Map what happens in this repo between a shopper pressing Pay and a courier being booked. One
> HTML file I can send to the team.

The repository: [`inputs/checkout/`](inputs/checkout/) — `docker-compose.yml`, `api/checkout.py`
(FastAPI), `worker/fulfil.py`.

## Output

[What a checkout request touches](checkout-map.html) — one page, opens offline.

The API prices the cart from Redis (falling back to Postgres), charges Stripe, records the order
and puts its id on a RabbitMQ queue; a separate worker books the courier and marks the order
booked. The shopper gets their answer before the courier is booked.

- **Assumed (dashed):** the shopper's browser and its POST — no client is in this repo.
- **Worth a look:** the worker reads `orders.address`, but the API's insert never writes one.
- **Left out:** other readers of the products table, and anything after the courier booking.

22 of 22 file citations checked against the repository.

## Why this is the right output

- Every box and arrow on the page cites the file and lines it came from; click one to see them.
- The two things the code does not show are drawn dashed, not stated as fact.
- The map answers the one question asked, and says what it left out.
- The page was built from [`checkout-map.json`](checkout-map.json) with
  `python3 scripts/build_diagram.py examples/checkout-map.json -o examples/checkout-map.html --repo-root examples/inputs/checkout`.

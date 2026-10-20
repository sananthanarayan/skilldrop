# Tidewater Grocers — order service (reliability review input)

Owner: Order team (engineering lead: Priya Raman). Product owner: Tom Okafor.
Head of Engineering: Dana Whitlock.

## What customers do with it

1. **Search and browse products** — web and app call `GET /products` and `GET /search`.
   About 4,800,000 requests a day. Customers abandon if results take more than about a second.
2. **Place an order (checkout)** — the customer presses "Place order". The app calls
   `POST /orders`, which validates the basket and puts the order on the `orders` queue
   (RabbitMQ), then returns `202 Accepted`. An `order-worker` takes it off the queue, charges
   the card through PayRail (our only payment provider, called synchronously from the worker)
   and writes the confirmation. The app polls `GET /orders/{id}` until it shows "confirmed"
   or "declined". About 240,000 `POST /orders` calls a day, including retries.
3. **Book a delivery slot** — `GET /slots` and `POST /slots/{id}/hold`. About 360,000 requests
   a day. If it fails the customer can usually try again a minute later.
4. **Store-ops admin API** — staff in 40 stores adjust stock and mark items unavailable.
   About 600 requests a day, nearly all between 08:00 and 16:00 on weekdays.

## What we measure today

- Load balancer access logs for every public endpoint: status code and total request time.
- `order_worker_process_seconds` histogram, timed inside the worker from the moment it takes an
  order off the queue until it writes the confirmation. The team proposes this as the checkout
  latency SLI ("p99 is 400 ms, we're in great shape").
- RabbitMQ `orders` queue depth.
- CPU, memory and pod restarts for every deployment.
- A browser beacon (real-user monitoring) on the search results page only.

## History (last 90 days, from load balancer logs)

| Journey | Success rate at the load balancer |
|---|---|
| Search and browse | 99.95% |
| `POST /orders` accepted | 99.97% |
| Delivery slots | 99.7% |
| Admin API | 99.6% (about 2 failed requests a week) |

On 14 September (a promotion day) the `orders` queue backed up for about 50 minutes. Queue wait
reached roughly 3 minutes and support logged 212 complaints about orders "stuck on processing".
`order_worker_process_seconds` p99 stayed at 400 ms throughout.

PayRail's published SLO is 99.9% monthly availability. PayRail had two incidents this quarter,
each around 40 minutes long.

## What we've been asked for

Tom wants checkout at **99.99%** "because checkout is revenue". Dana wants an error-budget
policy written down before the next quarter's planning. The admin API should have "the same
paging as everything else".

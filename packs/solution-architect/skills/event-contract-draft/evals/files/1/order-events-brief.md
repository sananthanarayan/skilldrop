# Order service: events we need to publish

From the order service team at Brightcart (fictional), for review with the platform team.

We want fulfilment and loyalty to stop polling our REST API every minute and react to events
instead. The platform team runs Kafka for us; topics default to 7 days' retention.

## Events we think we need

1. **CreateShipment** — we send this when an order has been paid, so the warehouse starts
   picking.
2. **OrderCancelled** — a customer or support agent cancels an order before it is dispatched.
3. **OrderPlaced** — we already publish this today on the topic `orders` (payload below), and
   fulfilment consumes it in production. In the next release we want to rename `total` to
   `totalAmount` and make it an integer in pence, to match the payments team's naming. We'd
   like to just change it in place so there's only one version to maintain.

## Who consumes what

- **Fulfilment** (warehouse system): needs the order id, the lines (SKU and quantity) and the
  delivery address. Starts picking only once the order is paid. Stops picking if it is
  cancelled.
- **Loyalty**: needs the customer id and the order total to award points, and takes the points
  back when an order is cancelled.
- **Analytics**: wants every order event from every order in one single global order, so their
  dashboards replay exactly as things happened across the whole business.

We'll put `customerEmail` on every event as well, just in case someone needs it later.

## What OrderPlaced looks like today

```json
{
  "orderId": "ord_7Q2K9",
  "customerId": "cus_31F8",
  "customerEmail": "jo.example@example.com",
  "total": 42.50,
  "currency": "GBP",
  "lines": [{ "sku": "TEA-EB-250", "quantity": 2 }],
  "deliveryAddress": { "line1": "1 Example Street", "town": "Exampleton", "postcode": "EX1 1AA" },
  "placedAt": "2026-10-19 14:03:11"
}
```

Nobody has decided yet who looks after failed messages.

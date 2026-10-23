# Example: Order placement across microservices

**Prompt the user gave:** *"Show me the sequence of calls when a customer places an order — we have an Order service, an Inventory service, a Payment service, and a Notification service."*

**Response:**

```mermaid
sequenceDiagram
    autonumber
    actor C as Customer
    participant W as Web frontend
    participant O as Order service
    participant I as Inventory service
    participant P as Payment service
    participant N as Notification service
    participant Q as Event bus

    C->>W: Click "Place order"
    W->>O: POST /orders
    O->>I: Reserve(items)
    alt items in stock
        I-->>O: ReservationId
        O->>P: Charge(amount, cardToken)
        alt payment OK
            P-->>O: PaymentId
            O->>Q: Publish OrderPlaced
            O-->>W: 201 Created
            W-->>C: "Order confirmed"
            Q-->>N: OrderPlaced
            N->>C: Email + push notification
        else payment declined
            P-->>O: 402 Declined
            O->>I: Release(reservationId)
            O-->>W: 402 Payment failed
            W-->>C: "Card declined"
        end
    else out of stock
        I-->>O: 409 OutOfStock
        O-->>W: 409 Unavailable
        W-->>C: "Sold out"
    end
```

**Design notes:**

- **Two-step inventory** (reserve → confirm) avoids the classic race where two customers buy the last unit between stock-check and charge.
- **Compensating action** (`Release`) on payment failure — explicit in the diagram so reviewers can spot the rollback gap if it's missing.
- **Notification is async** (event bus, dashed line) — slow email shouldn't block the customer's response.
- **`autonumber`** makes every step referenceable in design-review comments ("what happens at step 8?").

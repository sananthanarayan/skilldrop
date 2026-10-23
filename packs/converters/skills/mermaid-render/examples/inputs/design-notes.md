# Contoso order service: design notes

The request path:

```mermaid
flowchart LR
    Web([Web app]) -->|HTTPS| API[Order API]
    API --> DB[(Orders DB)]
    API -.publishes.-> Bus{{Event bus}}
```

What happens on checkout:

```mermaid
sequenceDiagram
    participant W as Web
    participant A as Order API
    W->>A: POST /orders
    alt stock reserved
        A-->>W: 201 Created
    else out of stock
        A-->>W: 409 Conflict
    end
```

The order lifecycle (has a mistake):

```mermaid
stateDiagram-v2
    [*] --> Placed
    state Fulfilment {
        Placed --> Packed
        Packed --> Shipped
    [*] --> Cancelled
```
